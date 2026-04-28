from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
import json

router = APIRouter(prefix="/summary", tags=["summary"])

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class SummaryRequest(BaseModel):
    consultation_notes: str
    patient_symptoms: str | None = None
    consultation_duration: int | None = None

class SummaryResponse(BaseModel):
    diagnosis_summary: str
    recommendations: str
    suggested_prescription: str
    follow_up: str
    full_summary: str

@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    try:
        prompt = f"""Tu es un assistant médical. Génère un résumé structuré de consultation médicale basé sur ces informations :

Notes de consultation : {request.consultation_notes}
Symptômes patient : {request.patient_symptoms or "Non renseignés"}
Durée de consultation : {request.consultation_duration or "Non renseignée"} minutes

Génère un résumé JSON avec exactement ces champs :
- diagnosis_summary : résumé du diagnostic en 2-3 phrases
- recommendations : recommandations médicales en 2-3 points
- suggested_prescription : prescription suggérée
- follow_up : suivi recommandé
- full_summary : compte-rendu complet en 1 paragraphe

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000,
        )

        result = json.loads(response.choices[0].message.content)
        return SummaryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))