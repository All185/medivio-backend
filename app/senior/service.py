from supabase import create_client
import os
from datetime import datetime

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Seuils de progression automatique
LEVEL_UP_THRESHOLD = 10  # 10 actions réussies pour passer au niveau suivant

async def get_or_create_profile(patient_id: str) -> dict:
    res = supabase.table("senior_profiles")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .execute()

    if res.data:
        return res.data[0]

    new_profile = supabase.table("senior_profiles").insert({
        "patient_id": patient_id,
        "autonomy_level": 1,
        "interactions_count": 0,
        "successful_actions": 0,
    }).execute()

    return new_profile.data[0]

async def record_interaction(patient_id: str, action: str, success: bool) -> dict:
    profile = await get_or_create_profile(patient_id)
    current_level = profile["autonomy_level"]

    # Enregistrer l'interaction
    supabase.table("senior_interactions").insert({
        "patient_id": patient_id,
        "action": action,
        "success": success,
        "level_at_time": current_level,
    }).execute()

    # Mettre à jour les compteurs
    new_interactions = profile["interactions_count"] + 1
    new_successful = profile["successful_actions"] + (1 if success else 0)

    # Vérifier progression de niveau
    new_level = current_level
    if new_successful >= LEVEL_UP_THRESHOLD * current_level and current_level < 3:
        new_level = current_level + 1

    supabase.table("senior_profiles").update({
        "interactions_count": new_interactions,
        "successful_actions": new_successful,
        "autonomy_level": new_level,
        "updated_at": datetime.now().isoformat(),
    }).eq("patient_id", patient_id).execute()

    return {
        "level": new_level,
        "leveled_up": new_level > current_level,
        "successful_actions": new_successful,
        "next_level_at": LEVEL_UP_THRESHOLD * new_level,
    }

async def set_level(patient_id: str, level: int) -> dict:
    """Permet au médecin d'ajuster manuellement le niveau"""
    await get_or_create_profile(patient_id)
    res = supabase.table("senior_profiles").update({
        "autonomy_level": level,
        "updated_at": datetime.now().isoformat(),
    }).eq("patient_id", patient_id).execute()
    return res.data[0]

async def get_family_access(patient_id: str) -> list:
    res = supabase.table("family_access")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .execute()
    return res.data

async def add_family_member(patient_id: str, family_email: str, family_name: str) -> dict:
    res = supabase.table("family_access").insert({
        "patient_id": patient_id,
        "family_email": family_email,
        "family_name": family_name,
    }).execute()
    return res.data[0]

async def remove_family_member(access_id: str) -> dict:
    res = supabase.table("family_access")\
        .delete()\
        .eq("id", access_id)\
        .execute()
    return {"success": True}

async def get_senior_dashboard(patient_id: str) -> dict:
    """Dashboard visible uniquement par médecin/famille"""
    profile = await get_or_create_profile(patient_id)

    interactions = supabase.table("senior_interactions")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .limit(20)\
        .execute()

    family = await get_family_access(patient_id)

    return {
        "profile": profile,
        "recent_interactions": interactions.data,
        "family_members": family,
    }