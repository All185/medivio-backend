from openai import AsyncOpenAI
from supabase import create_client
import os, json

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

async def analyze_emergency(symptoms: str, pain_level: int) -> dict:
    prompt = f"""Tu es un assistant médical d'orientation.
Symptômes du patient : {symptoms}
Niveau de douleur (1-10) : {pain_level}

Réponds UNIQUEMENT en JSON valide :
{{
  "level": "critical" | "urgent" | "standard",
  "recommendation": "texte court en français (max 2 phrases)"
}}

Règles :
- critical = menace vitale immédiate → appeler le 15 (SAMU)
- urgent = besoin de soins dans les 2h → téléconsultation prioritaire
- standard = peut attendre → consultation normale
"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

async def notify_doctor(patient_id: str, level: str) -> str | None:
    res = supabase.table("doctor_availability")\
        .select("doctor_id")\
        .eq("is_available", True)\
        .limit(1)\
        .execute()

    if not res.data:
        return None

    doctor_id = res.data[0]["doctor_id"]

    supabase.table("emergency_alerts").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "level": level,
        "acknowledged": False,
    }).execute()

    return doctor_id