import stripe
import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user
from app.billing.service import (
    create_invoice,
    get_patient_invoices,
    get_doctor_invoices,
    mark_invoice_paid,
    cancel_invoice,
    get_doctor_stats,
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/billing", tags=["billing"])

class CreateInvoiceRequest(BaseModel):
    patient_id: str
    amount: float
    description: str
    appointment_id: Optional[int] = None

@router.post("/create")
async def create(req: CreateInvoiceRequest, user=Depends(get_current_user)):
    return await create_invoice(
        doctor_id=user.id,
        patient_id=req.patient_id,
        amount=req.amount,
        description=req.description,
        appointment_id=req.appointment_id,
    )

@router.get("/patient")
async def get_patient(user=Depends(get_current_user)):
    return await get_patient_invoices(user.id)

@router.get("/doctor")
async def get_doctor(user=Depends(get_current_user)):
    return await get_doctor_invoices(user.id)

@router.get("/stats")
async def get_stats(user=Depends(get_current_user)):
    return await get_doctor_stats(user.id)

@router.patch("/pay/{invoice_id}")
async def pay(invoice_id: str, user=Depends(get_current_user)):
    return await mark_invoice_paid(invoice_id)

@router.patch("/cancel/{invoice_id}")
async def cancel(invoice_id: str, user=Depends(get_current_user)):
    return await cancel_invoice(invoice_id)

@router.post("/create-checkout/{invoice_id}")
async def create_checkout(invoice_id: str, user=Depends(get_current_user)):
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    res = supabase.table("invoices").select("*").eq("id", invoice_id).execute()
    if not res.data:
        return JSONResponse({"error": "Facture introuvable"}, status_code=404)
    invoice = res.data[0]
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": invoice["currency"].lower(),
                "product_data": {"name": invoice["description"]},
                "unit_amount": int(invoice["total"] * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"https://medivio-frontend.vercel.app/billing?success=true&invoice_id={invoice_id}",
        cancel_url=f"https://medivio-frontend.vercel.app/billing?cancelled=true",
        metadata={"invoice_id": invoice_id},
    )
    return {"checkout_url": session.url}

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception:
        return JSONResponse({"error": "Webhook invalide"}, status_code=400)

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        invoice_id = payment_intent.get("metadata", {}).get("invoice_id")
        if invoice_id:
            await mark_invoice_paid(invoice_id)

    return {"status": "ok"}

@router.get("/receipt/{invoice_id}")
async def get_receipt(invoice_id: str, user=Depends(get_current_user)):
    from app.billing.service import generate_receipt
    return await generate_receipt(invoice_id)

@router.get("/estimate/{total}")
async def get_estimate(total: float, user=Depends(get_current_user)):
    from app.billing.service import get_reimbursement_estimate
    return await get_reimbursement_estimate(total)