from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

POINTS_MAP = {
    "consultation": 100,
    "profile_completed": 50,
    "review_left": 30,
    "referral": 200,
    "daily_login": 10,
}

LEVELS = [
    {"name": "platine", "min": 2500, "discount": 15},
    {"name": "or", "min": 1000, "discount": 10},
    {"name": "argent", "min": 500, "discount": 5},
    {"name": "bronze", "min": 0, "discount": 0},
]

def get_level(total_points: int) -> dict:
    for level in LEVELS:
        if total_points >= level["min"]:
            return level
    return LEVELS[-1]

async def add_points(patient_id: str, action: str) -> dict:
    points = POINTS_MAP.get(action, 0)
    if points == 0:
        return {"error": "Action inconnue"}

    # Enregistrer l'action
    supabase.table("loyalty_points").insert({
        "patient_id": patient_id,
        "action": action,
        "points": points,
    }).execute()

    # Récupérer le total actuel
    existing = supabase.table("loyalty_levels")\
        .select("total_points")\
        .eq("patient_id", patient_id)\
        .execute()

    if existing.data:
        new_total = existing.data[0]["total_points"] + points
        supabase.table("loyalty_levels")\
            .update({"total_points": new_total, "level": get_level(new_total)["name"], "updated_at": "now()"})\
            .eq("patient_id", patient_id)\
            .execute()
    else:
        new_total = points
        supabase.table("loyalty_levels").insert({
            "patient_id": patient_id,
            "total_points": new_total,
            "level": get_level(new_total)["name"],
        }).execute()

    return {
        "points_earned": points,
        "total_points": new_total,
        "level": get_level(new_total),
    }

async def get_loyalty(patient_id: str) -> dict:
    # Niveau actuel
    level_res = supabase.table("loyalty_levels")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .execute()

    if not level_res.data:
        return {
            "total_points": 0,
            "level": LEVELS[-1],
            "history": [],
            "next_level": LEVELS[2],
            "points_to_next": 500,
        }

    total_points = level_res.data[0]["total_points"]
    current_level = get_level(total_points)

    # Historique
    history_res = supabase.table("loyalty_points")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()

    # Prochain niveau
    next_level = None
    points_to_next = 0
    for level in reversed(LEVELS):
        if level["min"] > total_points:
            next_level = level
            points_to_next = level["min"] - total_points
            break

    return {
        "total_points": total_points,
        "level": current_level,
        "history": history_res.data,
        "next_level": next_level,
        "points_to_next": points_to_next,
    }