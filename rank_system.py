import discord

RANKS = [
    {"min_points": 0, "role_name":"Novato","icon":"🌱"},
    {"min_points": 50, "role_name":"Makakinho","icon":"🐒"},
    {"min_points": 200, "role_name":"Legendario","icon":"🔥"},
    {"min_points": 500, "role_name":"Supremo","icon":"👑"},
    {"min_points": 10000, "role_name":"Goat","icon":"🐐"},
]



async def update_user_rank(member: discord.Member, points: int, guild: discord.Guild):
    new_rank = None
    for rank in reversed(RANKS):  # Desde rango más alto
        if points >= rank["min_points"]:
            new_rank = rank
            break
    if new_rank is None:
        return

    role = discord.utils.get(guild.roles, name=new_rank["role_name"])
    if role is None:
        print(f"El rol {new_rank['role_name']} no existe en el servidor.")
        return

    # Remover roles anteriores
    roles_to_remove = [discord.utils.get(guild.roles, name=r["role_name"]) for r in RANKS if r["role_name"] != new_rank["role_name"]]
    for r in roles_to_remove:
        if r in member.roles:
            await member.remove_roles(r)

    # Agregar nuevo rol
    if role not in member.roles:
        await member.add_roles(role)

    # Cambiar nickname con icono
    icon = new_rank["icon"]
    base_name = member.name
    if member.nick:
        base_name = member.nick
        for r in RANKS:
            base_name = base_name.replace(r["icon"], "").strip()
    new_nick = f"{icon} {base_name}"
    try:
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        print("No tengo permisos para cambiar el nickname")

def get_user_rank(member):
    for rank in RANKS:
        role = discord.utils.get(member.guild.roles, name=rank["role_name"])
        if role in member.roles:
            return rank
    return None

