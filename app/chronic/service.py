from supabase import create_client
import os
from datetime import datetime

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Seuils cliniques normaux
THRESHOLDS = {
    "blood_pressure_systolic": {"warning": 140, "critical": 180, "low": 90},
    "blood_pressure_diastolic": {"warning": 90, "critical": 120, "low": 60},
    "heart_rate": {"warning": 100, "critical": 130, "low": 50},
    "oxygen_saturation": {"warning": 95, "critical": 90, "low": None},
    "blood_glucose": {"warning": 180, "critical": 250, "low": 70},
    "temperature": {"warning": 38.0, "critical": 39.5, "low": 35.5},
}

def analyze_vitals(record: dict) -> list:
    alerts = []
    for field, thresholds in THRESHOLDS.items():
        value = record.get(field)
        if value is None:
            continue
        value = float(value)
        if thresholds.get("critical") and value >= thresholds["critical"]:
            alerts.append({
                "alert_type": field,
                "severity": "critical",
                "message": f"Valeur critique detectee : {field.replace('_', ' ')} = {value}",
            })
        elif thresholds.get("warning") and value >= thresholds["warning"]:
            alerts.append({
                "alert_type": field,
                "severity": "warning",
                "message": f"Valeur elevee : {field.replace('_', ' ')} = {value}",
            })
        elif thresholds.get("low") and value <= thresholds["low"]:
            alerts.append({
                "alert_type": field,
                "severity": "warning",
                "message": f"Valeur basse : {field.replace('_', ' ')} = {value}",
            })
    return alerts

async def add_vital_record(patient_id: str, data: dict) -> dict:
    data["patient_id"] = patient_id
    data["source"] = data.get("source", "manual")
    res = supabase.table("vital_records").insert(data).execute()
    record = res.data[0]

    alerts = analyze_vitals(data)
    for alert in alerts:
        alert["patient_id"] = patient_id
        alert["vital_record_id"] = record["id"]
        supabase.table("clinical_alerts").insert(alert).execute()

    return {"record": record, "alerts": alerts}

async def get_vital_records(patient_id: str, limit: int = 30) -> list:
    res = supabase.table("vital_records")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("recorded_at", desc=True)\
        .limit(limit)\
        .execute()
    return res.data

async def get_alerts(patient_id: str) -> list:
    res = supabase.table("clinical_alerts")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .eq("is_read", False)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def mark_alert_read(alert_id: str) -> dict:
    res = supabase.table("clinical_alerts")\
        .update({"is_read": True})\
        .eq("id", alert_id)\
        .execute()
    return res.data[0] if res.data else {}

async def get_doctor_patients_vitals(doctor_id: str) -> list:
    appointments = supabase.table("appointments")\
        .select("patient_id")\
        .eq("doctor_id", doctor_id)\
        .execute()

    patient_ids = list(set([a["patient_id"] for a in appointments.data]))
    if not patient_ids:
        return []

    results = []
    for patient_id in patient_ids:
        latest = supabase.table("vital_records")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("recorded_at", desc=True)\
            .limit(1)\
            .execute()

        alerts = supabase.table("clinical_alerts")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_read", False)\
            .execute()

        results.append({
            "patient_id": patient_id,
            "latest_record": latest.data[0] if latest.data else None,
            "unread_alerts": len(alerts.data),
        })

    return results