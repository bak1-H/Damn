import json
import os

points_file = "points.json"

def load_points():
    if not os.path.isfile(points_file):
        return {}
    with open(points_file, "r") as f:
        return json.load(f)

def save_points(points):
    with open(points_file, "w") as f:
        json.dump(points, f)

async def add_points(user_id, amount, member=None, guild=None):
    points = load_points()
    points[user_id] = points.get(user_id, 0) + amount
    save_points(points)
    if member and guild:
        from rank_system import update_user_rank
        await update_user_rank(member, points[user_id], guild)

def get_points(user_id):
    points = load_points()
    return points.get(user_id, 0)

def get_top(n=10):
    points = load_points()
    # Retorna una lista de tuplas (user_id, puntos) ordenada descendentemente
    return sorted(points.items(), key=lambda x: x[1], reverse=True)[:n]

def load_points():
    if not os.path.isfile(points_file):
        return {}
    try:
        with open(points_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}