import html
import logging
from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from core.config import settings
from services.whatsapp_service import wa_client
from services.ai_service import GemmaEngine
from api.reports import notify_staff_if_urgent

logger = logging.getLogger("sentry.webhook")

router = APIRouter(tags=["webhooks"])

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

    if report.get("status") == "error":
        return f"❌ *SENTRY AI WARNING*\n\n{report.get('message')}"

    notify_staff_if_urgent(report)

    if report["is_urgent"]:
        return f"🚨 *SENTRY EMERGENCY TRIAGE ALERT*\n\nReport classified as *URGENT ({report['category'].upper()})* in [{community_id}].\n\n*Cluster:* {report['cluster_id']}\n*Location:* {report['location']}\n*Action:* Escalated to Dispatcher."
    else:
        return f"✅ *SENTRY REPORT LOGGED*\n\nCommunity: *{community_id}*\nCategory: *{report['category'].upper()}*\nLocation: *{report['location']}*\nCluster: [{report['cluster_id']}]"

@router.get("/webhook/whatsapp")
async def verify_meta_webhook(request: Request):
    verify_token = settings.META_WA_VERIFY_TOKEN
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        logger.info("Meta WhatsApp Webhook verified!")
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Token mismatch")

@router.post("/webhook/whatsapp")
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

@router.post("/webhook/twilio")
async def handle_twilio_incoming_webhook(From: str = Form(...), Body: str = Form(...)):
    from_phone = From.replace("whatsapp:", "").strip()
    text_body = Body.strip()
    reply_text = process_whatsapp_text(text_body, sender_phone=from_phone)
    wa_client.send_text_message(from_phone, reply_text)

    safe_reply = html.escape(reply_text)
    twiml_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>"""
    return Response(content=twiml_xml, media_type="application/xml")

@router.post("/api/whatsapp/simulate")
async def whatsapp_simulator(
    From: str = Form("whatsapp:+2348123456789"),
    Body: str = Form(...),
    community_id: str = Form("kwasu_main")
):
    reply_msg = process_whatsapp_text(Body, sender_phone=From, community_id=community_id)
    return JSONResponse(content={"whatsapp_reply": reply_msg, "type": "response"})
