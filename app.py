import os
import json
import logging
import sqlite3
from fastapi import FastAPI, Request, Form, Query, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from database import get_db_connection, init_db
from sentry_engine import GemmaEngine
from whatsapp_client import WhatsAppClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentry.app")

app = FastAPI(
    title="Sentry — Multi-Community Intelligence Platform (Powered by Gemma 4)",
    description="Multi-tenant platform architecture supporting KWASU pilot, Malete Town, Ilorin, and beyond."
)

wa_client = WhatsAppClient()

@app.on_event("startup")
def startup_event():
    init_db()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Models
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

class TriageAction(BaseModel):
    action: str
    notes: str = ""
    actor: str = "Security Dispatcher"

# --- WEB UI & COMMUNITIES DIRECTORY ---

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/communities")
async def get_communities():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM communities ORDER BY name")
    comms = [dict(c) for c in cursor.fetchall()]
    conn.close()
    return {"communities": comms}

# --- WHATSAPP CLOUD & TWILIO WEBHOOKS ---

@app.get("/webhook/whatsapp")
async def verify_meta_webhook(request: Request):
    verify_token = os.getenv("META_WA_VERIFY_TOKEN", "sentry_kwasu_secret_2026")
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        logger.info("Meta WhatsApp Webhook verified!")
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Token mismatch")

@app.post("/webhook/whatsapp")
async def handle_meta_incoming_webhook(request: Request):
    try:
        body = await request.json()
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return JSONResponse(content={"status": "no_message"}, status_code=200)

        msg = messages[0]
        from_phone = msg.get("from")
        msg_type = msg.get("type")

        text_body = ""
        if msg_type == "text":
            text_body = msg.get("text", {}).get("body", "").strip()
        else:
            text_body = f"[{msg_type.upper()} message received]"

        reply_text = process_whatsapp_text(text_body, sender_phone=from_phone)
        wa_client.send_text_message(from_phone, reply_text)

        return JSONResponse(content={"status": "processed"}, status_code=200)

    except Exception as e:
        logger.error(f"Error handling Meta WhatsApp Webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)

@app.post("/webhook/twilio")
async def handle_twilio_incoming_webhook(From: str = Form(...), Body: str = Form(...)):
    from_phone = From.replace("whatsapp:", "").strip()
    text_body = Body.strip()
    reply_text = process_whatsapp_text(text_body, sender_phone=from_phone)
    wa_client.send_text_message(from_phone, reply_text)

    twiml_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
    return Response(content=twiml_xml, media_type="application/xml")

def process_whatsapp_text(text: str, sender_phone: str, community_id: str = "kwasu_main") -> str:
    clean_text = text.strip()
    lower_text = clean_text.lower()

    if lower_text in ["news", "brief", "updates", "status", "help"]:
        brief = GemmaEngine.generate_situation_brief(community_id=community_id)
        bullets = "\n• ".join(brief["summary_bullets"])
        return f"🟢 *SENTRY COMMUNITY BRIEF [{community_id.upper()}]*\n\n• {bullets}\n\n_Send any incident report to log it in real time._"

    if "?" in clean_text or lower_text.startswith("is ") or lower_text.startswith("where ") or lower_text.startswith("any "):
        rag_res = GemmaEngine.ask_rag(clean_text, community_id=community_id)
        citations_str = ", ".join(rag_res["citations"]) if rag_res["citations"] else "Live Reports"
        return f"🤖 *SENTRY AI BRAIN*\n\n{rag_res['answer']}\n\n📍 *Sources:* [{citations_str}]\n🛡️ *Community:* {community_id}"

    report = GemmaEngine.process_new_report(
        raw_text=clean_text,
        community_id=community_id,
        source_type="whatsapp",
        reporter_handle=f"WA Student ({sender_phone[-4:]})"
    )

    if report["is_urgent"]:
        return f"🚨 *SENTRY EMERGENCY TRIAGE ALERT*\n\nReport classified as *URGENT ({report['category'].upper()})* in [{community_id}].\n\n*Cluster:* {report['cluster_id']}\n*Location:* {report['location']}\n*Action:* Escalated to Dispatcher."
    else:
        return f"✅ *SENTRY REPORT LOGGED*\n\nCommunity: *{community_id}*\nCategory: *{report['category'].upper()}*\nLocation: *{report['location']}*\nCluster: [{report['cluster_id']}]"

# --- REST ENDPOINTS ---

@app.get("/api/reports")
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

    if category and category.lower() != "all":
        query += " AND category = %s"
        params.append(category.lower())

    if is_urgent is not None:
        query += " AND is_urgent = %s"
        params.append(1 if is_urgent else 0)

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

@app.post("/api/reports")
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
    return {"status": "success", "report": result}

@app.post("/api/ask")
async def ask_mode(query: AskQuery):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = GemmaEngine.ask_rag(query.question, community_id=query.community_id)
    return result

@app.get("/api/clusters")
async def get_clusters(community_id: str = Query("kwasu_main")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clusters WHERE community_id = %s ORDER BY updated_at DESC", (community_id,))
    clusters = [dict(c) for c in cursor.fetchall()]
    conn.close()
    return {"clusters": clusters, "community_id": community_id}

@app.get("/api/clusters/{cluster_id}")
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

@app.get("/api/situation-room")
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

@app.post("/api/admin/brief/generate")
async def generate_brief_admin(community_id: str = Query("kwasu_main")):
    brief = GemmaEngine.generate_situation_brief(community_id=community_id)
    return {"status": "success", "brief": brief}

@app.get("/api/admin/stats")
async def get_admin_stats(community_id: str = Query("kwasu_main")):
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

@app.get("/api/admin/urgent-queue")
async def get_urgent_queue(community_id: str = Query("kwasu_main")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE community_id = %s AND is_urgent = TRUE AND status != 'resolved' ORDER BY urgency_score DESC, created_at DESC", (community_id,))
    urgent_reports = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"urgent_reports": urgent_reports, "count": len(urgent_reports), "community_id": community_id}

@app.post("/api/admin/triage/{report_id}")
async def action_triage(report_id: int, payload: TriageAction):
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

@app.post("/api/whatsapp/simulate")
async def whatsapp_simulator(
    From: str = Form("whatsapp:+2348123456789"),
    Body: str = Form(...),
    community_id: str = Form("kwasu_main")
):
    reply_msg = process_whatsapp_text(Body, sender_phone=From, community_id=community_id)
    return JSONResponse(content={"whatsapp_reply": reply_msg, "type": "response"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
