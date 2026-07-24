# Sentry: AI-Powered Multi-Tenant Community Safety & Incident Intelligence Platform
## Kaggle Hackathon Technical Report & Proof of Work

**Selected Competition Track:** AI for Good / UN Sustainable Development Goals (SDGs)  
**Public Repository:** [GitHub Repository](https://github.com/olabisi-9ja/Sentry)  
**Live Demo App:** [https://sentry-7r67.onrender.com](https://sentry-7r67.onrender.com)  

---

### Executive Summary & Impact Narrative

In many developing regions, university campuses, and local municipal sectors, community safety reporting is fragmented, slow, and unreliable. Citizens often face hurdles when reporting emergencies—from lack of accessible channels to fear of privacy loss.

**Sentry** bridges this critical gap. It is an AI-powered, multi-tenant community intelligence assistant designed to help citizens report, classify, prioritize, and respond to incidents seamlessly via WhatsApp and Web interfaces. Built around **Gemma 4**, Sentry transforms raw, unstructured noise into structured, actionable intelligence for dispatchers while directly advancing UN Sustainable Development Goals:
- **SDG 11 (Sustainable Cities & Communities):** Provides zero-friction public safety reporting infrastructure for underserved campus and municipal zones.
- **SDG 3 (Good Health & Well-being):** Reduces emergency dispatch latency through real-time AI urgency triaging.
- **SDG 16 (Peace, Justice & Strong Institutions):** Enhances institutional responsiveness, transparency, and citizen trust through automated PII redaction and audit logs.

---

### Technical Architecture & System Design

Sentry utilizes a clean, modular backend architecture built with **FastAPI** and **Pydantic**, coupled with a **React** frontend and a hybrid **PostgreSQL / SQLite** multi-tenant database layer.

```
[Citizen User] ---> (WhatsApp / Web UI)
                          |
                          v
         [Omni-Channel Webhook / API Router]
                          |
                          v
              [PII Sanitization Layer]
                          |
                          v
              [Gemma 4 AI Engine Service]
            /             |             \
 [Structured Triage]  [Grounded RAG]  [Situation Briefs]
            \             |             /
                          v
               [Multi-Tenant Database]
                          |
                          v
         [Dispatcher Situation Dashboard]
```

#### Core Components:
1. **Omni-Channel Ingestion Router:** Intercepts incoming messages from Meta WhatsApp Cloud API, Twilio Webhooks, and web clients.
2. **PII Sanitizer:** Intercepts text before sending prompts to the LLM, scrubbing phone numbers, emails, and account identifiers to preserve anonymity.
3. **Gemma 4 AI Engine:** Manages structured classification, RAG document grounding, and executive situation brief synthesis.
4. **Multi-Tenant Database Engine:** Segregates reports, clusters, and situation briefs by `community_id` (e.g., `kwasu_main`, `malete_town`, `ilorin_central`).

---

### Specific Gemma 4 Implementation

Gemma 4 is the core cognitive layer of Sentry. We leveraged Gemma 4 across three distinct operational modes:

1. **Structured Incident Triage (`gemma-4-12b-it`):**
   Gemma 4 parses raw, unstructured incident messages and emits strictly typed JSON conforming to our system schema:
   - **Category Taxonomy:** Auto-classifies into `security`, `power`, `water`, `transport`, `sanitation`, `road_conditions`, or `community_patrol`.
   - **Severity & Urgency Scoring:** Assigns a 1–5 severity index and computes an urgency probability score (0.0 to 1.0) to flag emergencies immediately.
   - **Entity Extraction:** Extracts normalized location identifiers.

2. **Grounded Retrieval-Augmented Generation (RAG):**
   When citizens ask questions via WhatsApp (e.g., *"Is there any water supply issue in Hostel Block A?"*), Gemma 4 queries recent community records, acting as a zero-hallucination Q&A engine grounded strictly in verified report context.

3. **Executive Situation Room Synthesis (`gemma-4-31b-it`):**
   For dispatchers and administrators, Gemma 4 synthesizes active incident clusters into executive bulleted briefs, providing situational awareness in seconds.

4. **Local Open-Weights Fallback (Ollama Integration):**
   Sentry natively supports local execution via Ollama (`gemma:4`). This allows campus security stations to run Sentry fully offline or in low-connectivity scenarios where internet connection is intermittent.

---

### Sprint Challenges & Solutions

During our 1-day sprint, we overcame several key engineering challenges:

1. **API Latency & Unreliable Connectivity:**
   - *Challenge:* Real-time WhatsApp webhooks require immediate responses (under 5 seconds).
   - *Solution:* Implemented an inline rule-engine fallback (`_fallback_classify_and_triage`) inside `services/ai_service.py` that guarantees high availability and zero downtime if external API calls timeout.

2. **Multi-Tenancy Isolation:**
   - *Challenge:* Preventing data leakages between adjacent communities sharing the same backend.
   - *Solution:* Parameterized database queries and isolated schema structures scoped strictly by `community_id`.

3. **Privacy & Anonymity:**
   - *Challenge:* Users sending WhatsApp messages expose their personal phone numbers.
   - *Solution:* Applied regex-based PII sanitization at entry before passing data to Gemma or persisting to disk, storing only anonymized student handles (e.g., `WA Student (8900)`).

---

### Why Our Technical Choices Were Right

- **FastAPI & Pydantic:** Provides async request execution, automatic schema validation, and lightning-fast OpenAPI documentation.
- **Gemma 4:** Open-weights capability guarantees data privacy, edge deployment suitability, and lower long-term inference costs compared to proprietary APIs.
- **React + Vite:** Provides a slick, responsive mobile-first UI for both citizens and dispatchers.
- **Dual Database Strategy:** Enables lightweight zero-config local testing via SQLite and high-concurrency production scaling on PostgreSQL with zero code changes.

---

### Conclusion & Project Links

Sentry demonstrates how Gemma 4 can power a complete, end-to-end community safety workflow—moving far beyond standard chat widgets into meaningful, real-world societal impact.

- **Source Code Repository:** [GitHub - olabisi-9ja/Sentry](https://github.com/olabisi-9ja/Sentry)
- **Live Demo Application:** [https://sentry-7r67.onrender.com](https://sentry-7r67.onrender.com)
