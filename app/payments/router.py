from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.config import settings
from app.auth.models import UserOut
from app.auth.dependencies import get_current_user
from app.payments.models import CheckoutCreate, CheckoutOut, WebhookResponse
from supabase import create_client, Client
import stripe
import os 

router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)


@router.post("/checkout", response_model=CheckoutOut, status_code=201)
async def create_checkout(
    body: CheckoutCreate,
    current_user: UserOut = Depends(get_current_user)
):
    """Crée une session Stripe Checkout pour un rendez-vous."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency":     body.currency,
                    "unit_amount":  body.amount,
                    "product_data": {
                        "name": "Consultation médicale",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={
                "appointment_id": body.appointment_id,
                "patient_id":     current_user.id,
            }
        )
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    return CheckoutOut(
        checkout_url=session.url,
        session_id=session.id,
    )


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(request: Request):
    """Reçoit les événements Stripe et met à jour le statut du rendez-vous."""
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Paiement réussi → confirmer le rendez-vous
    if event["type"] == "checkout.session.completed":
        session        = event["data"]["object"]
        appointment_id = session["metadata"].get("appointment_id")

        if appointment_id:
            supabase.table("appointments")\
                .update({"status": "confirmed"})\
                .eq("id", appointment_id)\
                .execute()

    return WebhookResponse(status="ok")