import discord
from discord.ext import commands
import asyncio
from yt_dlp import YoutubeDL
import os
import lyricsgenius
import requests
import re
import aiohttp
from bs4 import BeautifulSoup
from puntos import add_points, get_points, get_top
from datetime import datetime
import json
import puntos
from rank_system import update_user_rank, get_user_rank
import rank_system

GENIUS_TOKEN=os.getenv("GENIUS_TOKEN")
TOKEN=os.getenv("TOKEN")
is_looping = False
current_info = None




intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ydl_opts = {
    'format': 'bestaudio/best/bestvideo+bestaudio',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',
}

ydl = YoutubeDL(ydl_opts)

voice_client = None
queue = []
is_playing = False
is_looping = False
current_song_info = None

async def extract_info(url):
    # Ejecutar la extracción en hilo separado para no bloquear asyncio
    return await asyncio.to_thread(ydl.extract_info, url, False)

def create_source(info):
    url = info['url']
    return discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')

async def play_next(ctx):
    global is_playing, voice_client, is_looping, current_song_info

    if is_looping and current_song_info:
        # Reproducir la misma canción de nuevo
        source = create_source(current_song_info)
        voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"🔁 Reproduciendo nuevamente: {current_song_info['title']}")
        return

    if len(queue) == 0:
        is_playing = False
        await ctx.send("🐒 La cola ha terminado, cotito.")
        return

    is_playing = True
    current_song_info = queue.pop(0)
    source = create_source(current_song_info)
    voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"🎵 Reproduciendo: {current_song_info['title']}")



@bot.command()
async def play(ctx, url: str):
    global voice_client, is_playing

    if ctx.author.voice is None:
        await ctx.send("🐒Debes estar en un canal para poner un temita.")
        return

    if voice_client is None or not voice_client.is_connected():
        voice_client = await ctx.author.voice.channel.connect()
    elif voice_client.channel != ctx.author.voice.channel:
        await voice_client.move_to(ctx.author.voice.channel)

    try:
        info = await extract_info(url)
    except Exception as e:
        await ctx.send(f"🐒No pude extraer la info: {e}")
        return

    queue.append(info)
    await ctx.send(f"🐒Se agrego : {info['title']} a la playlist!")

    if not is_playing:
        await play_next(ctx)

@bot.command()
async def skip(ctx):
    global voice_client, is_playing

    if voice_client is None or not voice_client.is_playing():
        await ctx.send("🐒No hay tema activo!.")
        return

    voice_client.stop()
    await ctx.send("🐒Se saltaron el temita.")

@bot.command()
async def stop(ctx):
    global voice_client, is_playing, queue

    if voice_client is None:
        await ctx.send("🐒No estoy conectado a ni una weá.")
        return

    queue.clear()
    is_playing = False
    await voice_client.disconnect()
    voice_client = None
    await ctx.send("🐒Reproducción detenida, CHAO.")


@bot.command()
async def loop(ctx):
    global is_looping
    is_looping = not is_looping
    if is_looping:
        await ctx.send("🔁 Bucle del tema: ✅.")
    else:
        await ctx.send("🔁 Bucle del tema: ❌.")
        
CLIENT_ACCESS_TOKEN = "kPiumkph-WUsL-By7GgoP3CMbpihdOjOJrKc-KAdk2fthoq1mLIqHas3SWu3xT8f"
current_song_title = None


def clean_title(title):
    title = re.sub(r"[\(\[].*?[\)\]]", "", title)
    title = re.sub(r"\b(ft|feat|featuring)\b.*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\b(prod(uced)? by)\b.*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"[^\x00-\x7F]+", "", title)
    title = re.sub(r"\s{2,}", " ", title).strip()
    return title

@bot.command(name="lyrics")
async def lyrics(ctx):
    if not current_song_title:
        await ctx.send("🐒 No hay ninguna canción reproduciéndose.")
        return

    cleaned_title = clean_title(current_song_title)

    search_url = "https://api.genius.com/search"
    headers = {
        "Authorization": "Bearer kPiumkph-WUsL-By7GgoP3CMbpihdOjOJrKc-KAdk2fthoq1mLIqHas3SWu3xT8f"  # <-- Reemplaza con tu token real
    }
    params = {"q": cleaned_title}

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=headers, params=params) as response:
            if response.status != 200:
                await ctx.send("🐒 Error al consultar Genius. Código de estado: " + str(response.status))
                print(f"🔴 Error de Genius API ({response.status}): {await response.text()}")
                return

            data = await response.json()
            if "response" not in data or "hits" not in data["response"]:
                await ctx.send("🐒 No se pudo obtener resultados de Genius.")
                print(f"🔴 Respuesta inesperada: {data}")
                return

            hits = data["response"]["hits"]
            if not hits:
                await ctx.send("🐒 No encontré la letra en Genius.")
                return

            song_url = hits[0]["result"]["url"]

        # Obtener letra desde la página web
        async with session.get(song_url) as lyrics_response:
            html = await lyrics_response.text()
            soup = BeautifulSoup(html, "lxml")
            lyrics_divs = soup.select("div[data-lyrics-container='true']")
            lyrics = "\n".join([div.get_text(separator="\n").strip() for div in lyrics_divs])

    if not lyrics:
        await ctx.send("🐒 No pude obtener la letra de la canción.")
        return

    # Dividir si es demasiado larga
    chunks = [lyrics[i:i + 2000] for i in range(0, len(lyrics), 2000)]
    for chunk in chunks:
        await ctx.send(f"LETRA DEL TEMITA")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if amount < 1:
        await ctx.send("🐒 Como que 0 aweonao?.")
        return
    deleted = await ctx.channel.purge(limit=amount+1)  # +1 para borrar el mensaje del comando
    await ctx.send(f"🐒 He borrado {len(deleted)-1} mensajes.", delete_after=5)



@bot.command()
async def ayuda(ctx):
    embed = discord.Embed(title="Comandos disponibles", color=0x00ff00)
    embed.add_field(name="!play <url>", value="Reproduce una canción desde una URL.", inline=False)
    embed.add_field(name="!skip", value="Salta la canción actual.", inline=False)
    embed.add_field(name="!stop", value="Detiene la reproducción y desconecta al bot.", inline=False)
    embed.add_field(name="!loop", value="Activa o desactiva el bucle de la canción actual.", inline=False)
    embed.add_field(name="!lyrics", value="Muestra la letra de la canción actual.", inline=False)
    embed.add_field(name="!clear <n>", value="Borra los últimos (n) mensajes del canal.", inline=False)
    embed.add_field(name="!encuesta <pregunta>", value="Crea una encuesta con la pregunta dada.", inline=False)
    embed.add_field(name="!top", value="Muestra el top 10 de usuarios con más puntos.", inline=False)
    embed.add_field(name="!ayuda", value="Muestra esta ayuda.", inline=False)
    embed.add_field(name="!rango", value="Muestra tu rango actual.", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def encuesta(ctx, *, question):
    message = await ctx.send(f"📊{question}")
    await message.add_reaction("👍")
    await message.add_reaction("👎")


@bot.command()
async def top(ctx):
    top_users = get_top(10)
    if not top_users:
        await ctx.send("🐒 No hay puntos registrados aún.")
        return

    mensaje = "🏆 Top 10 usuarios con más puntos:\n"
    for i, (user_id, pts) in enumerate(top_users, start=1):
        user = await bot.fetch_user(int(user_id))
        mensaje += f"{i}. {user.name}: {pts} puntos\n"

    await ctx.send(mensaje)

@bot.command()
async def rango(ctx):
    """Muestra el rango del usuario actual y actualiza el nickname con el icono."""
    user_id = str(ctx.author.id)
    puntos = get_points(user_id)
    # ACTUALIZA el rango y el nickname según los puntos
    await update_user_rank(ctx.author, puntos, ctx.guild)
    rank = get_user_rank(ctx.author)
    rank_name = rank["role_name"] if rank else "Sin rango💀"
    icon = rank["icon"] if rank else ""

    await ctx.send(f"{icon} **{ctx.author.display_name}**\nPuntos: **{puntos}**\nRango: **{rank_name}**")
BONUS_VOICE_CHANNEL = "Juegos"
LAST_BONUS_FILE = "last_bonus.json"
BONUS_POINTS = 10

def load_last_bonus():
    if not os.path.isfile(LAST_BONUS_FILE):
        return {}
    try:
        with open(LAST_BONUS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}
    

def save_last_bonus(data):
    with open(LAST_BONUS_FILE, "w") as f:
        json.dump(data, f)

@bot.event
async def on_voice_state_update(member, before, after):
    # Solo si entra a un canal de voz
    if after.channel and after.channel.name == BONUS_VOICE_CHANNEL:
        last_bonus = load_last_bonus()
        user_id = str(member.id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if last_bonus.get(user_id) != today:
            # Da puntos y actualiza el registro
            await add_points(user_id, BONUS_POINTS, member=member, guild=member.guild)
            last_bonus[user_id] = today
            save_last_bonus(last_bonus)
            try:
                await member.send(f"🎮 ¡Has recibido {BONUS_POINTS} puntos por entrar a {BONUS_VOICE_CHANNEL} hoy!")
            except Exception:
                pass
    
@bot.event
async def on_member_join(member):
    """Asigna el rol inicial y actualiza el nickname al entrar un usuario nuevo."""
    from rank_system import RANKS
    # Primer rango (el de menor min_points)
    initial_rank = RANKS[0]
    role = discord.utils.get(member.guild.roles, name=initial_rank["role_name"])
    if role:
        await member.add_roles(role)
    # Cambia el nickname con el icono del rango
    icon = initial_rank["icon"]
    base_name = member.name
    new_nick = f"{icon} {base_name}"
    try:
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        pass  # No hay permisos para cambiar el nick



bot.run(TOKEN)
