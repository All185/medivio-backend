from supabase import create_client
from openai import AsyncOpenAI
import os
import json
from datetime import datetime

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUESTIONNAIRES = {
    "Dermatologie": ["Depuis combien de temps ?", "La lesion s'etend-elle ?", "Y a-t-il des demangeaisons ?", "Avez-vous de la fievre ?", "Avez-vous des allergies connues ?"],
    "Cardiologie": ["Avez-vous des douleurs thoraciques ?", "Avez-vous des palpitations ?", "Etes-vous essoufle au repos ?", "Avez-vous des antecedents cardiaques ?"],
    "Medecine generale": ["Depuis combien de temps ?", "Avez-vous de la fievre ?", "Prenez-vous des medicaments ?", "Avez-vous des allergies ?", "Avez-vous consulte recemment ?"],
    "Gynecologie": ["Quel est votre cycle habituel ?", "Avez-vous des douleurs ?", "Y a-t-il des saignements anormaux ?", "Etes-vous enceinte ou pourriez-vous l'etre ?"],
    "Psychiatrie": ["Depuis combien de temps ressentez-vous cela ?", "Dormez-vous normalement ?", "Avez-vous des pensees envahissantes ?", "Prenez-vous un traitement ?"],
    "default": ["Depuis combien de temps ?", "Intensite de 1 a 10 ?", "Avez-vous de la fievre ?", "Prenez-vous des medicaments ?", "Avez-vous des allergies ?"],
}

async def triage_case(chief_complaint: str, answers: dict) -> dict:
    prompt = f"""Tu es un assistant medical de triage.
Motif de consultation : {chief_complaint}
Reponses questionnaire : {json.dumps(answers, ensure_ascii=False)}

Reponds UNIQUEMENT en JSON valide :
{{
  "triage_level": "async" | "video" | "emergency",
  "triage_reason": "explication courte (1 phrase)",
  "ai_summary": "resume clinique structure en 2-3 phrases pour le medecin"
}}

Regles :
- emergency = danger vital immediat
- video = cas complexe necessitant examen visuel en temps reel
- async = cas simple pouvant etre traite en differentiel
"""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)

async def create_case(patient_id: str, specialty: str, chief_complaint: str, symptoms: list, answers: dict) -> dict:
    triage = await triage_case(chief_complaint, answers)

    res = supabase.table("async_cases").insert({
        "patient_id": patient_id,
        "specialty": specialty,
        "chief_complaint": chief_complaint,
        "symptoms": symptoms,
        "questionnaire_answers": answers,
        "triage_level": triage["triage_level"],
        "triage_reason": triage["triage_reason"],
        "ai_summary": triage["ai_summary"],
        "status": "pending",
    }).execute()

    return res.data[0]

async def get_patient_cases(patient_id: str) -> list:
    res = supabase.table("async_cases")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def get_doctor_cases(doctor_id: str) -> list:
    res = supabase.table("async_cases")\
        .select("*")\
        .in_("status", ["pending", "in_review"])\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def get_case(case_id: str) -> dict | None:
    res = supabase.table("async_cases")\
        .select("*")\
        .eq("id", case_id)\
        .execute()
    if not res.data:
        return None
    case = res.data[0]
    messages = supabase.table("async_messages")\
        .select("*")\
        .eq("case_id", case_id)\
        .order("created_at")\
        .execute()
    case["messages"] = messages.data
    return case

async def respond_to_case(case_id: str, doctor_id: str, response: str) -> dict:
    supabase.table("async_cases").update({
        "doctor_id": doctor_id,
        "doctor_response": response,
        "status": "answered",
        "answered_at": datetime.now().isoformat(),
    }).eq("id", case_id).execute()

    supabase.table("async_messages").insert({
        "case_id": case_id,
        "sender_id": doctor_id,
        "sender_role": "doctor",
        "message": response,
    }).execute()

    return {"success": True}

async def escalate_case(case_id: str) -> dict:
    res = supabase.table("async_cases")\
        .update({"status": "escalated", "triage_level": "video"})\
        .eq("id", case_id)\
        .execute()
    return res.data[0] if res.data else {}

def get_questionnaire(specialty: str) -> list:
    return QUESTIONNAIRES.get(specialty, QUESTIONNAIRES["default"])