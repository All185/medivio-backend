import os
import json
from fastapi import APIRouter, HTTPException, status, Depends
from app.config import settings
from app.auth.models import UserOut
from app.auth.dependencies import get_current_user
from app.triage.models import TriageRequest, TriageOut
from supabase import create_client, Client
from mistralai import Mistral
 
router = APIRouter(prefix="/triage", tags=["triage"])
 
mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
 
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)
 
 
@router.post("/", response_model=TriageOut, status_code=201)
async def create_triage(
    body: TriageRequest,
    current_user: UserOut = Depends(get_current_user)
):
    """Analyse les symptômes du patient et génère un résumé pour le médecin."""
 
    prompt = f"""Tu es un assistant médical. Analyse les symptômes suivants et génère un résumé structuré pour le médecin.
 
Symptômes : {body.symptoms}
Durée : {body.duration}
Sévérité (1-10) : {body.severity}
Antécédents médicaux : {body.medical_history or "Aucun renseigné"}
 
Réponds en JSON avec exactement ces champs :
- summary : résumé clinique en 2-3 phrases
- urgency_level : "low", "medium" ou "high"
- recommendations : conseils pour le médecin en 1-2 phrases
 
Réponds UNIQUEMENT avec le JSON, sans texte autour."""
 
    try:
        response = await mistral_client.chat.complete_async(
            model="mistral-small-latest",
            messages=[
                {
                    "role":    "system",
                    "content": "Tu es un assistant médical qui aide les médecins à préparer leurs consultations."
                },
                {
                    "role":    "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
 
    try:
        result = json.loads(response.choices[0].message.content)
    except Exception:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur de parsing de la réponse Mistral"
        )
 
    # Sauvegarder le triage dans Supabase
    supabase.table("appointments").update({
        "notes": f"TRIAGE IA:\n{result['summary']}\nUrgence: {result['urgency_level']}\n{result['recommendations']}"
    }).eq("id", body.appointment_id).execute()
 
    return TriageOut(
        appointment_id=body.appointment_id,
        summary=result["summary"],
        urgency_level=result["urgency_level"],
        recommendations=result["recommendations"],
    )