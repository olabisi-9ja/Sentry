from fastapi import APIRouter, Query, HTTPException, Header, Depends
from pydantic import BaseModel
from database.connection import get_db_connection
from services.ai_service import GemmaEngine
from core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

class TriageAction(BaseModel):
    action: str
    notes: str = ""
    actor: str = "Security Dispatcher"

def verify_admin(x_admin_passcode: str = Header(None)):
    expected_passcode = settings.ADMIN_PASSCODE
    if not expected_passcode:
        raise HTTPException(status_code=500, detail="Admin passcode not configured on server")
        
    if x_admin_passcode != expected_passcode:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Admin Passcode")

@router.post("/brief/generate")
async def generate_brief_admin(community_id: str = Query("kwasu_main"), admin: None = Depends(verify_admin)):
    brief = GemmaEngine.generate_situation_brief(community_id=community_id, model="gemma-4-31b-it")
    return {"status": "success", "brief": brief}

@router.get("/stats")
async def get_admin_stats(community_id: str = Query("kwasu_main"), admin: None = Depends(verify_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM reports WHERE community_id = %s", (community_id,))
    total_reports = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as open FROM clusters WHERE community_id = %s AND status = 'active'", (community_id,))
    open_clusters = cursor.fetchone()["open"]

    cursor.execute("SELECT COUNT(*) as urgent FROM reports WHERE community_id = %s AND is_urgent = TRUE AND status = 'open'", (community_id,))
    urgent_unresolved = cursor.fetchone()["urgent"]

    cursor.execute("SELECT category, COUNT(*) as cat_count FROM reports WHERE community_id = %s GROUP BY category", (community_id,))
    category_counts = {row["category"]: row["cat_count"] for row in cursor.fetchall()}

    conn.close()

    return {
        "community_id": community_id,
        "open_incidents": open_clusters,
        "urgent_unresolved": urgent_unresolved,
        "total_reports": total_reports,
        "avg_response_time": "5.4m",
        "campus_status": "HIGH ALERT" if urgent_unresolved > 2 else ("ELEVATED" if urgent_unresolved > 0 else "NORMAL"),
        "category_distribution": category_counts
    }

@router.get("/urgent-queue")
async def get_urgent_queue(community_id: str = Query("kwasu_main"), admin: None = Depends(verify_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE community_id = %s AND is_urgent = TRUE AND status != 'resolved' ORDER BY urgency_score DESC, created_at DESC", (community_id,))
    urgent_reports = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"urgent_reports": urgent_reports, "count": len(urgent_reports), "community_id": community_id}

@router.post("/triage/{report_id}")
async def action_triage(report_id: int, payload: TriageAction, admin: None = Depends(verify_admin)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
    report = cursor.fetchone()
    if not report:
        conn.close()
        raise HTTPException(status_code=404, detail="Report not found.")

    new_status = payload.action
    if payload.action == 'dispatch':
        new_status = 'dispatched'

    cursor.execute("UPDATE reports SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s", (new_status, report_id))

    cursor.execute("""
        INSERT INTO admin_actions (report_id, action, notes, actor)
        VALUES (%s, %s, %s, %s)
    """, (report_id, payload.action, payload.notes or f"Action set to {new_status}", payload.actor))

    conn.commit()
    conn.close()

    return {"status": "success", "report_id": report_id, "new_status": new_status}
