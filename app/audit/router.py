from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.auth.dependencies import get_current_user
from app.database import get_supabase
from typing import Optional

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


async def log_action(
    supabase: Client,
    user_id: str,
    action: str,
    table_name: str,
    record_id: Optional[str] = None,
    old_data: Optional[dict] = None,
    new_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    """Enregistre une action dans le journal d'audit."""
    supabase.table("audit_log").insert({
        "user_id": user_id,
        "action": action,
        "table_name": table_name,
        "record_id": str(record_id) if record_id else None,
        "old_data": old_data,
        "new_data": new_data,
        "ip_address": ip_address,
    }).execute()


@router.get("/logs")
async def get_audit_logs(
    table_name: Optional[str] = None,
    limit: int = 100,
    current_user=Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
):
    """Récupère le journal d'audit (admin uniquement)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")

    query = supabase.table("audit_log").select("*").order("created_at", desc=True).limit(limit)
    if table_name:
        query = query.eq("table_name", table_name)

    result = query.execute()
    return result.data