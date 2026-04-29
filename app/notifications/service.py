import resend
import os

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_appointment_confirmation(patient_email: str, patient_name: str, doctor_name: str, scheduled_at: str):
    try:
        resend.Emails.send({
            "from": "Medivio <onboarding@resend.dev>",
            "to": patient_email,
            "subject": "Confirmation de votre rendez-vous — Medivio",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2563EB, #6366F1); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Medivio</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Télémédecine accessible à tous</p>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                    <h2 style="color: #1E293B;">✅ Rendez-vous confirmé</h2>
                    <p style="color: #64748B;">Bonjour <strong>{patient_name}</strong>,</p>
                    <p style="color: #64748B;">Votre rendez-vous a été confirmé avec succès.</p>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #2563EB;">
                        <p style="margin: 0; color: #1E293B;"><strong>📅 Date :</strong> {scheduled_at}</p>
                        <p style="margin: 8px 0 0; color: #1E293B;"><strong>👨‍⚕️ Médecin :</strong> Dr. {doctor_name}</p>
                    </div>
                    <p style="color: #64748B;">Connectez-vous sur Medivio quelques minutes avant votre consultation.</p>
                    <a href="https://medivio-frontend.vercel.app/dashboard" 
                       style="display: inline-block; background: #2563EB; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px;">
                        Accéder à mon tableau de bord
                    </a>
                    <p style="color: #94A3B8; font-size: 12px; margin-top: 20px;">Medivio — La télémédecine accessible à tous</p>
                </div>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False

def send_appointment_reminder(patient_email: str, patient_name: str, doctor_name: str, scheduled_at: str):
    try:
        resend.Emails.send({
            "from": "Medivio <onboarding@resend.dev>",
            "to": patient_email,
            "subject": "Rappel — Votre consultation Medivio dans 1 heure",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2563EB, #6366F1); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Medivio</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Rappel de consultation</p>
                </div>
                <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                    <h2 style="color: #1E293B;">⏰ Rappel — Consultation dans 1 heure</h2>
                    <p style="color: #64748B;">Bonjour <strong>{patient_name}</strong>,</p>
                    <p style="color: #64748B;">Votre consultation avec Dr. <strong>{doctor_name}</strong> commence dans <strong>1 heure</strong>.</p>
                    <div style="background: #FEF3C7; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #1E293B;"><strong>📅 Date :</strong> {scheduled_at}</p>
                        <p style="margin: 8px 0 0; color: #1E293B;"><strong>👨‍⚕️ Médecin :</strong> Dr. {doctor_name}</p>
                    </div>
                    <p style="color: #64748B;">Préparez-vous en remplissant votre fiche pré-consultation.</p>
                    <a href="https://medivio-frontend.vercel.app/waiting" 
                       style="display: inline-block; background: #2563EB; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px;">
                        Accéder à la salle d'attente
                    </a>
                    <p style="color: #94A3B8; font-size: 12px; margin-top: 20px;">Medivio — La télémédecine accessible à tous</p>
                </div>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        return False