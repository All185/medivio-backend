import os
from mistralai import Mistral
import json
from supabase import create_client

mistral_client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))


async def analyze_emergency(symptoms: str, pain_level: int) -> dict:
    prompt = f"""You are a medical triage assistant. Analyze the following emergency:
Symptoms: {symptoms}
Pain level: {pain_level}/10

Respond with a JSON object with these exact keys:
- level: one of "critical", "urgent", "moderate"
- recommendation: a short actionable recommendation in French

Rules:
- critical: pain >= 8 or life-threatening symptoms (chest pain, difficulty breathing, loss of consciousness)
- urgent: pain 5-7 or severe symptoms
- moderate: pain < 5 and manageable symptoms"""

    response = await mistral_client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


async def notify_doctor(patient_id: str, level: str) -> str | None:
    res = supabase.table("doctors")\
        .select("id")\
        .eq("available", True)\
        .limit(1)\
        .execute()

    if not res.data:
        return None

    doctor_id = res.data[0]["id"]

    supabase.table("notifications").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "type": "emergency",
        "level": level,
        "read": False,
    }).execute()

    return doctor_id
