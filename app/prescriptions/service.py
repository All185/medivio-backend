from supabase import create_client
import os
import secrets

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

async def create_prescription(doctor_id: str, patient_id: str, items: list, notes: str) -> dict:
    # Générer un token sécurisé unique
    token = secrets.token_urlsafe(32)

    # Créer la prescription
    prescription = supabase.table("prescriptions").insert({
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "token": token,
        "notes": notes,
        "status": "active",
    }).execute()

    prescription_id = prescription.data[0]["id"]

    # Ajouter les médicaments
    for item in items:
        supabase.table("prescription_items").insert({
            "prescription_id": prescription_id,
            "medication": item["medication"],
            "dosage": item["dosage"],
            "frequency": item["frequency"],
            "duration": item["duration"],
            "instructions": item.get("instructions", ""),
        }).execute()

    return {
        "id": prescription_id,
        "token": token,
        "status": "active",
    }

async def get_patient_prescriptions(patient_id: str) -> list:
    res = supabase.table("prescriptions")\
        .select("*, prescription_items(*)")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def get_doctor_prescriptions(doctor_id: str) -> list:
    res = supabase.table("prescriptions")\
        .select("*, prescription_items(*)")\
        .eq("doctor_id", doctor_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def verify_prescription(token: str) -> dict | None:
    res = supabase.table("prescriptions")\
        .select("*, prescription_items(*)")\
        .eq("token", token)\
        .execute()

    if not res.data:
        return None

    return res.data[0]

async def dispense_prescription(token: str) -> dict:
    res = supabase.table("prescriptions")\
        .update({"status": "dispensed"})\
        .eq("token", token)\
        .execute()
    return res.data[0] if res.data else {}