from fastapi import APIRouter, Depends
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