from supabase import create_client
from openai import AsyncOpenAI
import os
import json

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SPECIALTIES = [
    "Cardiologie", "Dermatologie", "Neurologie", "Psychiatrie",
    "Pediatrie", "Gynecologie", "Ophtalmologie", "ORL",
    "Orthopédie", "Gastro-enterologie", "Endocrinologie",
    "Pneumologie", "Rhumatologie", "Urologie", "Medecine generale"
]

async def get_all_specialists(specialty: str = None, city: str = None) -> list:
    query = supabase.table("specialist_profiles").select("*")
    if specialty:
        query = query.eq("specialty", specialty)
    if city:
        query = query.ilike("city", f"%{city}%")
    query = query.order("average_rating", desc=True)
    res = query.execute()
    return res.data

async def get_specialist(specialist_id: str) -> dict | None:
    res = supabase.table("specialist_profiles")\
        .select("*")\
        .eq("id", specialist_id)\
        .execute()
    if not res.data:
        return None
    specialist = res.data[0]
    reviews = supabase.table("specialist_reviews")\
        .select("*")\
        .eq("specialist_id", specialist_id)\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    specialist["reviews"] = reviews.data
    return specialist

async def create_specialist_profile(data: dict) -> dict:
    res = supabase.table("specialist_profiles").insert(data).execute()
    return res.data[0]

async def claim_profile(specialist_id: str, user_id: str) -> dict:
    res = supabase.table("specialist_profiles").update({
        "user_id": user_id,
        "is_claimed": True,
    }).eq("id", specialist_id).execute()
    return res.data[0]

async def add_review(specialist_id: str, patient_id: str, rating: int, comment: str) -> dict:
    supabase.table("specialist_reviews").insert({
        "specialist_id": specialist_id,
        "patient_id": patient_id,
        "rating": rating,
        "comment": comment,
    }).execute()

    reviews = supabase.table("specialist_reviews")\
        .select("rating")\
        .eq("specialist_id", specialist_id)\
        .execute()

    avg = sum(r["rating"] for r in reviews.data) / len(reviews.data)
    supabase.table("specialist_profiles").update({
        "average_rating": round(avg, 2),
        "total_reviews": len(reviews.data),
    }).eq("id", specialist_id).execute()

    return {"success": True, "new_average": round(avg, 2)}

async def match_specialist(symptoms: str) -> dict:
    prompt = f"""Tu es un assistant médical d'orientation.
Le patient décrit : {symptoms}

Réponds UNIQUEMENT en JSON valide :
{{
  "specialty": "une des spécialités suivantes : {', '.join(SPECIALTIES)}",
  "urgency": "low | medium | high",
  "reason": "explication courte en français (1 phrase)"
}}
"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    specialists = await get_all_specialists(specialty=result["specialty"])
    return {
        "specialty": result["specialty"],
        "urgency": result["urgency"],
        "reason": result["reason"],
        "specialists": specialists[:5],
    }