import json
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from database.connection import get_db_connection
from services.ai_service import GemmaEngine
from services.whatsapp_service import wa_client
from core.config import settings

router = APIRouter(prefix="/api", tags=["reports"])

class ReportCreate(BaseModel):
    text: str
    location: str = "General Sector Grounds"
    community_id: str = "kwasu_main"
    category: str = None
    anonymous: bool = True
    source_type: str = "web"

class AskQuery(BaseModel):
    question: str
    community_id: str = "kwasu_main"

def notify_staff_if_urgent(report: dict):
    if report.get("is_urgent") and settings.SECURITY_STAFF_WHATSAPP_NUMBER:
        alert = (f"🚨 SENTRY URGENT — {report['category'].upper()}\n"
                 f"Location: {report['location']}\nConfidence: {report['confidence_score']}%\n"
                 f"Cluster: {report['cluster_id']}\nReport: {report['anonymized_text']}")
        wa_client.send_text_message(settings.SECURITY_STAFF_WHATSAPP_NUMBER, alert)

@router.get("/communities")
async def get_communities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM communities ORDER BY name")
    comms = [dict(c) for c in cursor.fetchall()]
    conn.close()
    return {"communities": comms}

@router.get("/reports")
async def get_reports(
    community_id: str = Query("kwasu_main"),
    category: str = Query(None),
    is_urgent: bool = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    cluster_id: str = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM reports WHERE community_id = %s"
    params = [community_id]

    if category and isinstance(category, str) and category.lower() != "all":
        query += " AND category = %s"
        params.append(category.lower())

    if is_urgent is not None:
        query += " AND is_urgent = %s"
        params.append(bool(is_urgent))

    if status:
        query += " AND status = %s"
        params.append(status)

    if cluster_id:
        query += " AND cluster_id = %s"
        params.append(cluster_id)

    if search:
        query += " AND (raw_text LIKE %s OR location LIKE %s OR anonymized_text LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    reports = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {"reports": reports, "count": len(reports), "community_id": community_id}

@router.post("/reports")
async def create_report(payload: ReportCreate):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Report text cannot be empty.")

    reporter_handle = "Anon Student" if payload.anonymous else "Verified Member"
    
    result = GemmaEngine.process_new_report(
        raw_text=payload.text,
        community_id=payload.community_id,
        location=payload.location,
        source_type=payload.source_type,
        reporter_handle=reporter_handle
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    notify_staff_if_urgent(result)
    return {"status": "success", "report": result}

@router.post("/ask")
async def ask_mode(query: AskQuery):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = GemmaEngine.ask_rag(query.question, community_id=query.community_id)
    return result

@router.get("/clusters")
async def get_clusters(community_id: str = Query("kwasu_main")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clusters WHERE community_id = %s ORDER BY updated_at DESC", (community_id,))
    clusters = [dict(c) for c in cursor.fetchall()]
    conn.close()
    return {"clusters": clusters, "community_id": community_id}

@router.get("/clusters/{cluster_id}")
async def get_cluster_detail(cluster_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clusters WHERE id = %s", (cluster_id,))
    cluster_row = cursor.fetchone()
    if not cluster_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Cluster not found.")

    cluster = dict(cluster_row)
    cursor.execute("SELECT * FROM reports WHERE cluster_id = %s ORDER BY created_at DESC", (cluster_id,))
    linked_reports = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {"cluster": cluster, "reports": linked_reports}

@router.get("/situation-room")
async def get_situation_room(community_id: str = Query("kwasu_main")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM briefs WHERE community_id = %s ORDER BY generated_at DESC LIMIT 1", (community_id,))
    latest_brief = cursor.fetchone()
    conn.close()

    if not latest_brief:
        brief = GemmaEngine.generate_situation_brief(community_id=community_id)
        return brief

    brief = dict(latest_brief)
    try:
        brief["summary_bullets"] = json.loads(brief["summary_bullets"])
    except:
        pass
    return brief
