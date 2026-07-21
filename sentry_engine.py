import os
import re
import json
import requests
from datetime import datetime
from database import get_db_connection

class GemmaEngine:
    """
    Sentry Gemma 4 Engine with Multi-Community Tenant Support (`community_id`),
    Expanded Off-Campus Category Taxonomy, and Grounded RAG.
    """

    CATEGORIES = {
        "security": ["security", "thief", "lock", "stolen", "suspicious", "fight", "gate broken", "threat", "gun", "knife", "attack", "robbery", "harass", "patrol"],
        "power": ["power", "light", "electricity", "blackout", "transformer", "wire", "generator", "socket", "dark", "outage", "spark", "current"],
        "water": ["water", "tap", "pipe", "tank", "dry", "plumbing", "leak", "borehole", "flush", "pump", "drainage"],
        "transport": ["shuttle", "bus", "transport", "cab", "ride", "gate stop", "driver", "stranding", "commute", "fare", "traffic"],
        "sanitation": ["trash", "waste", "garbage", "bin", "drain", "dirty", "smell", "dump", "cleaning", "overflow", "refuse"],
        "road_conditions": ["road", "pothole", "flooding", "erosion", "bridge", "tar", "asphalt", "gutter", "blockage"],
        "community_patrol": ["vigilante", "community watch", "patrol", "neighborhood watch", "checkpoint", "night watch"]
    }

    LOCATION_KEYWORDS = {
        "Hostel Block C": ["block c", "hostel c", "hall c"],
        "Hostel Block D": ["block d", "hostel d", "hall d"],
        "Hostel Block A": ["block a", "hostel a"],
        "Hostel Block B": ["block b", "hostel b"],
        "Hall B Hostel": ["hall b", "hallb"],
        "Engineering Gate": ["engr gate", "engineering gate", "engineering building", "engr"],
        "Main Gate Stop": ["main gate", "gate stop", "shuttle stop"],
        "Library Annex": ["library", "lib", "library annex"],
        "Senate Building": ["senate", "admin building"],
        "Lecture Hall C": ["hall c", "lecture hall c"],
        "Malete Central Market": ["malete market", "market square", "malete central"],
        "Ilorin Expressway Junction": ["expressway", "junction", "ilorin road"]
    }

    @staticmethod
    def sanitize_pii(text: str) -> str:
        text = re.sub(r'(\+?234|0)[789][01]\d{8}', '[PHONE REDACTED]', text)
        text = re.sub(r'\b\d{10,11}\b', '[NUMBER REDACTED]', text)
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', text)
        return text.strip()

    @classmethod
    def call_live_gemma_llm(cls, prompt: str, system_instruction: str = "") -> str:
        groq_key = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMMA_API_KEY")

        if groq_key:
            try:
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gemma2-9b-it",
                    "messages": [
                        {"role": "system", "content": system_instruction or "You are Sentry AI powered by Gemma 4 for community intelligence."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=8)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
            except Exception as e:
                pass

        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemma-4-31b-it:generateContent?key={gemini_key}"
                payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}]}
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                print(f"Gemini API Error: {e}")
                pass

        return None

    @classmethod
    def classify_and_triage(cls, raw_text: str, custom_location: str = None) -> dict:
        anonymized_text = cls.sanitize_pii(raw_text)
        
        system_instruction = """You are Sentry AI. Your job is to classify and triage community incident reports.
You must return your response as a valid JSON object without any markdown formatting.
The JSON must contain the following keys:
- "category": (string) one of ["security", "power", "water", "transport", "sanitation", "road_conditions", "community_patrol"]
- "severity": (integer) 1 to 5 (5 is most severe)
- "urgency_score": (float) 0.0 to 1.0 (1.0 is most urgent)
- "is_urgent": (boolean) true if immediate action is needed, else false
- "location": (string) extracted from the text, or a general area if not specific
- "confidence_score": (integer) 0 to 100 based on how clear the report is
"""
        prompt = f"Analyze this report and provide the JSON.\nRaw report: '{anonymized_text}'\nCustom location hint: {custom_location or 'None'}"
        
        try:
            response_text = cls.call_live_gemma_llm(prompt, system_instruction)
            if response_text:
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                triage_data = json.loads(response_text)
                return {
                    "anonymized_text": anonymized_text,
                    "category": triage_data.get("category", "security"),
                    "severity": int(triage_data.get("severity", 2)),
                    "urgency_score": round(float(triage_data.get("urgency_score", 0.5)), 2),
                    "is_urgent": bool(triage_data.get("is_urgent", False)),
                    "location": triage_data.get("location", "Unknown Location"),
                    "confidence_score": int(triage_data.get("confidence_score", 80))
                }
        except Exception as e:
            print(f"LLM Classification failed: {e}")
            
        return cls._fallback_classify_and_triage(anonymized_text, raw_text, custom_location)

    @classmethod
    def _fallback_classify_and_triage(cls, anonymized_text: str, raw_text: str, custom_location: str = None) -> dict:
        lower_text = raw_text.lower()

        category_scores = {cat: 0 for cat in cls.CATEGORIES}
        for cat, keywords in cls.CATEGORIES.items():
            for kw in keywords:
                if kw in lower_text:
                    category_scores[cat] += 1

        selected_category = max(category_scores, key=category_scores.get)
        if category_scores[selected_category] == 0:
            selected_category = "security" if any(w in lower_text for w in ["help", "urgent", "danger", "thief", "attack"]) else "power"

        location = custom_location or "General Sector Grounds"
        if not custom_location or custom_location == "Auto-Detect":
            for loc_name, keywords in cls.LOCATION_KEYWORDS.items():
                if any(kw in lower_text for kw in keywords):
                    location = loc_name
                    break

        urgency_score = 0.35
        severity = 2
        is_urgent = False

        if selected_category == "security" or selected_category == "community_patrol":
            urgency_score = 0.88
            severity = 5
            is_urgent = True
        elif "broken" in lower_text or "dark" in lower_text or "2 days" in lower_text or "flooded" in lower_text or "pothole" in lower_text:
            urgency_score = 0.80
            severity = 4
            is_urgent = True
        elif "dry" in lower_text or "leak" in lower_text:
            urgency_score = 0.65
            severity = 3
        elif "trash" in lower_text or "shuttle" in lower_text:
            urgency_score = 0.40
            severity = 2

        if any(w in lower_text for w in ["urgent", "emergency", "danger", "immediately", "help", "threat", "fire"]):
            urgency_score = min(0.99, urgency_score + 0.25)
            severity = min(5, severity + 1)
            is_urgent = True

        confidence_score = 90 + min(9, (len(raw_text.split()) // 3))

        return {
            "anonymized_text": anonymized_text,
            "category": selected_category,
            "severity": severity,
            "urgency_score": round(urgency_score, 2),
            "is_urgent": is_urgent,
            "location": location,
            "confidence_score": confidence_score
        }

    @classmethod
    def find_or_create_cluster(cls, conn, community_id: str, category: str, location: str, text: str, severity: int) -> tuple:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, category, report_count, summary FROM clusters
            WHERE community_id = %s AND category = %s AND status = 'active'
        """, (community_id, category))
        active_clusters = cursor.fetchall()

        for cluster in active_clusters:
            if location.lower() in cluster["title"].lower() or location.lower() in cluster["summary"].lower() or category == cluster["category"]:
                c_id = cluster["id"]
                new_count = cluster["report_count"] + 1
                cursor.execute("""
                    UPDATE clusters SET report_count = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s
                """, (new_count, c_id))
                return c_id, f"Clustered with {new_count} similar reports in {community_id}. {cluster['summary']}"

        cursor.execute("SELECT COUNT(*) as count FROM clusters;")
        c_num = cursor.fetchone()["count"] + 101
        new_c_id = f"CLUST-{c_num}"
        new_title = f"{category.replace('_', ' ').capitalize()} Issue — {location}"
        new_summary = f"Incident reported at {location}: '{text[:60]}...'"

        cursor.execute("""
            INSERT INTO clusters (id, community_id, title, category, primary_location, severity, status, report_count, summary)
            VALUES (%s, %s, %s, %s, %s, %s, 'active', 1, %s)
        """, (new_c_id, community_id, new_title, category, location, severity, new_summary))

        return new_c_id, f"New incident log created [{new_c_id}] for community [{community_id}]."

    @classmethod
    def process_new_report(cls, raw_text: str, community_id: str = "kwasu_main", location: str = None, source_type: str = "web", reporter_handle: str = "Anon Student") -> dict:
        triage = cls.classify_and_triage(raw_text, location)

        conn = get_db_connection()
        cluster_id, cluster_note = cls.find_or_create_cluster(
            conn, community_id, triage["category"], triage["location"], raw_text, triage["severity"]
        )

        if triage["is_urgent"]:
            ai_reply = f"🚨 URGENT FLAG ({triage['confidence_score']}% confidence): Escalated to Dispatch / Community Liaisons. {cluster_note}"
        else:
            ai_reply = f"Verified report ({triage['confidence_score']}% confidence). {cluster_note}"

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (community_id, raw_text, anonymized_text, category, severity, urgency_score, is_urgent, location, cluster_id, status, confidence_score, source_type, reporter_handle, ai_reply)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'open', %s, %s, %s, %s)
        """, (
            community_id,
            raw_text,
            triage["anonymized_text"],
            triage["category"],
            triage["severity"],
            triage["urgency_score"],
            1 if triage["is_urgent"] else 0,
            triage["location"],
            cluster_id,
            triage["confidence_score"],
            source_type,
            reporter_handle,
            ai_reply
        ))

        report_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
        report_row = dict(cursor.fetchone())
        conn.close()

        return report_row

    @classmethod
    def ask_rag(cls, question: str, community_id: str = "kwasu_main") -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()

        q_lower = question.lower()
        keywords = [w for w in re.findall(r'\w+', q_lower) if len(w) > 3 and w not in ["what", "where", "is", "there", "have", "this", "that", "from", "with"]]

        if not keywords:
            cursor.execute("SELECT * FROM reports WHERE community_id = %s ORDER BY created_at DESC LIMIT 5", (community_id,))
        else:
            query_parts = []
            params = [community_id]
            for kw in keywords:
                query_parts.append("(raw_text LIKE %s OR location LIKE %s OR category LIKE %s)")
                params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
            
            sql = f"SELECT * FROM reports WHERE community_id = %s AND ({' OR '.join(query_parts)}) ORDER BY created_at DESC LIMIT 6"
            cursor.execute(sql, params)

        matched_reports = [dict(r) for r in cursor.fetchall()]

        if not matched_reports:
            cursor.execute("SELECT * FROM reports WHERE community_id = %s ORDER BY created_at DESC LIMIT 3", (community_id,))
            matched_reports = [dict(r) for r in cursor.fetchall()]

        conn.close()

        citations = list(set([r["cluster_id"] for r in matched_reports if r.get("cluster_id")]))
        locations = list(set([r["location"] for r in matched_reports]))

        if not matched_reports:
            ans = "I do not have any recent reports regarding that issue in the database."
            confidence = 0
        else:
            context = "\n".join([f"- Report: {r['anonymized_text']} (Location: {r['location']}, Category: {r['category']})" for r in matched_reports])
            system_instruction = "You are a helpful AI assistant summarizing community reports based on the provided context. Provide a conversational, concise, and helpful answer based ONLY on the data. Do NOT hallucinate info not in the reports."
            prompt = f"Context from recent reports in {community_id}:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            
            try:
                ans = cls.call_live_gemma_llm(prompt, system_instruction)
                if not ans:
                    raise Exception("No response from LLM")
                confidence = 96
            except Exception as e:
                print(f"LLM RAG failed: {e}")
                r_summaries = "; ".join([r['anonymized_text'] for r in matched_reports[:2]])
                ans = f"Sentry intelligence for [{community_id}]: '{r_summaries}'."
                confidence = 50

        return {
            "question": question,
            "answer": ans,
            "citations": citations,
            "locations": locations,
            "matched_count": len(matched_reports),
            "confidence_score": confidence,
            "community_id": community_id,
            "sources": matched_reports
        }

    @classmethod
    def generate_situation_brief(cls, community_id: str = "kwasu_main") -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clusters WHERE community_id = %s AND status != 'resolved' ORDER BY severity DESC", (community_id,))
        clusters = [dict(c) for c in cursor.fetchall()]

        overall_status = "ELEVATED" if any(c["severity"] >= 4 for c in clusters) else "MODERATE"

        if not clusters:
            bullets = [f"All sector operational in {community_id}. No active incident clusters flagged."]
        else:
            context = "\n".join([f"- {c['title']} (Severity: {c['severity']}, Count: {c['report_count']}): {c['summary']}" for c in clusters])
            system_instruction = "You are a security intelligence AI. Based on the active clusters provided, write a concise, bulleted executive summary of the current situation. Provide ONLY the bullets starting with '- ' or '* '."
            prompt = f"Active Clusters in {community_id}:\n{context}\n\nProvide the bulleted summary."
            
            try:
                ans = cls.call_live_gemma_llm(prompt, system_instruction)
                if ans:
                    bullets = [b.strip("-* ").strip() for b in ans.split("\n") if b.strip("-* ").strip()]
                    if not bullets:
                        raise Exception("Failed to parse bullets")
                else:
                    raise Exception("No response from LLM")
            except Exception as e:
                print(f"LLM Brief generation failed: {e}")
                bullets = [f"{c['title']} ({c['report_count']} reports linked) — Status: {c['status'].upper()}." for c in clusters]

        summary_json = json.dumps(bullets)

        cursor.execute("""
            INSERT INTO briefs (community_id, period_title, summary_bullets, overall_status)
            VALUES (%s, %s, %s, %s)
        """, (community_id, f"Sentry Community Intelligence Brief [{community_id}]", summary_json, overall_status))

        conn.commit()
        conn.close()

        brief = {
            "community_id": community_id,
            "period_title": f"Sentry Intelligence Brief [{community_id}]",
            "summary_bullets": bullets,
            "overall_status": overall_status,
            "generated_at": datetime.now().strftime("%I:%M %p, %b %d")
        }

        return brief
