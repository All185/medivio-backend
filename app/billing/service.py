from supabase import create_client
import os
from datetime import datetime

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

LOYALTY_DISCOUNTS = {
    "bronze": 0,
    "argent": 5,
    "or": 10,
    "platine": 15,
}

def generate_invoice_number() -> str:
    now = datetime.now()
    return f"MED-{now.strftime('%Y%m%d%H%M%S')}"

async def get_patient_loyalty_discount(patient_id: str) -> float:
    res = supabase.table("loyalty_levels")\
        .select("level")\
        .eq("patient_id", patient_id.strip())\
        .execute()
    if not res.data:
        return 0
    level = res.data[0]["level"]
    return LOYALTY_DISCOUNTS.get(level, 0)

async def create_invoice(doctor_id: str, patient_id: str, amount: float, description: str, appointment_id: int = None) -> dict:
    discount_percent = await get_patient_loyalty_discount(patient_id)
    discount_amount = round(amount * discount_percent / 100, 2)
    total = round(amount - discount_amount, 2)
    invoice_number = generate_invoice_number()

    invoice = supabase.table("invoices").insert({
        "invoice_number": invoice_number,
        "doctor_id": doctor_id,
        "patient_id": patient_id.strip(),
        "appointment_id": appointment_id,
        "amount": amount,
        "discount": discount_amount,
        "total": total,
        "description": description,
        "status": "pending",
    }).execute()

    return invoice.data[0]

async def get_patient_invoices(patient_id: str) -> list:
    res = supabase.table("invoices")\
        .select("*")\
        .eq("patient_id", patient_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def get_doctor_invoices(doctor_id: str) -> list:
    res = supabase.table("invoices")\
        .select("*")\
        .eq("doctor_id", doctor_id)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

async def mark_invoice_paid(invoice_id: str) -> dict:
    res = supabase.table("invoices")\
        .update({"status": "paid", "paid_at": datetime.now().isoformat()})\
        .eq("id", invoice_id)\
        .execute()
    return res.data[0] if res.data else {}

async def cancel_invoice(invoice_id: str) -> dict:
    res = supabase.table("invoices")\
        .update({"status": "cancelled"})\
        .eq("id", invoice_id)\
        .execute()
    return res.data[0] if res.data else {}

async def get_doctor_stats(doctor_id: str) -> dict:
    res = supabase.table("invoices")\
        .select("*")\
        .eq("doctor_id", doctor_id)\
        .execute()
    
    invoices = res.data
    total_revenue = sum(i["total"] for i in invoices if i["status"] == "paid")
    pending_amount = sum(i["total"] for i in invoices if i["status"] == "pending")
    total_invoices = len(invoices)
    paid_invoices = len([i for i in invoices if i["status"] == "paid"])

    now = datetime.now()
    monthly_revenue = sum(
        i["total"] for i in invoices
        if i["status"] == "paid" and
        datetime.fromisoformat(i["paid_at"].replace("Z", "")).month == now.month
        if i.get("paid_at")
    )

    return {
        "total_revenue": total_revenue,
        "pending_amount": pending_amount,
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "monthly_revenue": monthly_revenue,
    }

async def generate_receipt(invoice_id: str) -> dict:
    res = supabase.table("invoices").select("*").eq("id", invoice_id).execute()
    if not res.data:
        return {}
    invoice = res.data[0]
    
    # Taux de remboursement standard Assurance Maladie
    AM_RATE = 0.70  # 70% remboursé par l'AM
    am_reimbursement = round(invoice["total"] * AM_RATE, 2)
    patient_share = round(invoice["total"] - am_reimbursement, 2)

    return {
        "invoice_number": invoice["invoice_number"],
        "description": invoice["description"],
        "amount": invoice["amount"],
        "discount": invoice["discount"],
        "total": invoice["total"],
        "currency": invoice["currency"],
        "status": invoice["status"],
        "created_at": invoice["created_at"],
        "paid_at": invoice.get("paid_at"),
        "am_reimbursement": am_reimbursement,
        "patient_share": patient_share,
        "am_rate": int(AM_RATE * 100),
    }

async def get_reimbursement_estimate(total: float) -> dict:
    AM_RATE = 0.70
    am_reimbursement = round(total * AM_RATE, 2)
    patient_share = round(total - am_reimbursement, 2)
    return {
        "total": total,
        "am_reimbursement": am_reimbursement,
        "patient_share": patient_share,
        "am_rate": 70,
    }
    