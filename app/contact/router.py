from fastapi import APIRouter
from pydantic import BaseModel
import resend
import os

router = APIRouter()
resend.api_key = os.environ.get("RESEND_API_KEY")

class ContactForm(BaseModel):
    name: str
    email: str
    organization: str = ""
    message: str

@router.post("/contact")
async def send_contact(form: ContactForm):
    try:
        resend.Emails.send({
            "from": "Medivio <contact@medivio.care>",
            "to": "contact@medivio.care",
            "reply_to": form.email,
            "subject": f"Nouveau message de contact — {form.name}",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Medivio</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Nouveau message de contact</p>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                    <h2 style="color: #1E293B;">📩 Nouveau message</h2>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #2B5EF8;">
                        <p style="margin: 0; color: #1E293B;"><strong>Nom :</strong> {form.name}</p>
                        <p style="margin: 8px 0 0; color: #1E293B;"><strong>Email :</strong> {form.email}</p>
                        {"<p style='margin: 8px 0 0; color: #1E293B;'><strong>Organisation :</strong> " + form.organization + "</p>" if form.organization else ""}
                    </div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0; color: #1E293B;"><strong>Message :</strong></p>
                        <p style="margin: 8px 0 0; color: #64748B; white-space: pre-wrap;">{form.message}</p>
                    </div>
                    <p style="color: #94A3B8; font-size: 12px; margin-top: 20px;">Medivio — contact@medivio.care</p>
                </div>
            </div>
            """
        })
        return {"success": True}
    except Exception as e:
        print(f"Erreur envoi contact: {e}")
        return {"success": False}
