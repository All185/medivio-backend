from fastapi import APIRouter, Header, HTTPException
from supabase import create_client
import resend
import os
from datetime import datetime, timezone, timedelta

router = APIRouter()
resend.api_key = os.environ.get("RESEND_API_KEY")

supabase = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
)

def send_trial_email(email: str, full_name: str, days_left: int):
    if days_left == 30:
        subject = "Votre période d'essai Medivio se termine dans 30 jours"
        message = "Il vous reste <strong>30 jours</strong> pour profiter de votre accès gratuit complet à Medivio."
    elif days_left == 7:
        subject = "Plus que 7 jours d'essai gratuit sur Medivio"
        message = "Votre période d'essai se termine dans <strong>7 jours</strong>. Contactez-nous pour continuer à utiliser Medivio."
    else:
        subject = "Votre période d'essai Medivio a expiré"
        message = "Votre période d'essai gratuite est terminée. Contactez-nous pour discuter de votre abonnement."

    resend.Emails.send({
        "from": "Medivio <contact@medivio.care>",
        "to": email,
        "subject": subject,
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Medivio</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Télémédecine augmentée par l'IA</p>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                <h2 style="color: #1E293B;">Bonjour Dr. {full_name},</h2>
                <p style="color: #64748B;">{message}</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://medivio.care/contact" style="display: inline-block; background: linear-gradient(135deg, #009E88, #2B5EF8); color: white; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: bold;">
                        Nous contacter
                    </a>
                </div>
                <p style="color: #94A3B8; font-size: 12px; text-align: center;">Medivio — <a href="https://medivio.care" style="color: #2B5EF8;">medivio.care</a></p>
            </div>
        </div>
        """
    })

@router.post("/trial/check")
async def check_trials(x_cron_secret: str = Header(None)):
    secret = os.environ.get("CRON_SECRET", "")
    if x_cron_secret != secret:
        raise HTTPException(status_code=401, detail="Non autorisé")

    try:
        res = supabase.table("specialist_profiles").select("user_id, trial_start_date").execute()
        profiles = res.data or []
        now = datetime.now(timezone.utc)
        sent = 0

        for profile in profiles:
            trial_start = profile.get("trial_start_date")
            user_id = profile.get("user_id")
            if not trial_start or not user_id:
                continue

            start = datetime.fromisoformat(trial_start.replace("Z", "+00:00"))
            end = start + timedelta(days=90)
            days_left = (end - now).days

            if days_left in [30, 7, 0]:
                user_res = supabase.auth.admin.get_user_by_id(user_id)
                if user_res and user_res.user:
                    email = user_res.user.email
                    full_name = (user_res.user.user_metadata or {}).get("full_name", "")
                    send_trial_email(email, full_name, days_left)
                    sent += 1

        return {"success": True, "emails_sent": sent}
    except Exception as e:
        return {"success": False, "error": str(e)}
