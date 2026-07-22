# Sentry Protocol

Sentry is an AI-powered, multi-tenant community intelligence platform. It ingests unstructured incident reports from multiple sources (WhatsApp, Web), categorizes them using **Gemma 4**, extracts critical context (severity, location), and routes urgent threats directly to a live Situation Room Dashboard.

## Core Features
1. **Gemma 4 AI Engine:** Sentry strictly utilizes `gemma-4-31b-it` via the Gemini API to parse unstructured text, identify emergencies, and provide triage actions.
2. **Multi-Tenant Architecture:** Built from the ground up to support multiple communities (e.g., `kwasu_main`, `ilorin_central`) within a single unified database.
3. **Omni-Channel Ingestion:** Intercepts live reports via Twilio WhatsApp Webhooks and direct Web App submissions.
4. **Secure Admin Triage:** Administrator-only protected routes for dispatching responders and synthesizing RAG-powered situation briefs.

## Live Demo
**Dashboard URL:** [https://sentry-7r67.onrender.com](https://sentry-7r67.onrender.com)
**WhatsApp Node:** Send `Hello` to our Twilio Sandbox number to submit a live report.

*Note: As this is hosted on a free Render tier, the initial request might take up to 30 seconds if the instance is waking up from sleep. Wait 15 seconds and try again for instant response times.*

## Architecture
- **Backend:** Python FastAPI
- **Database:** PostgreSQL (Production) / SQLite (Local)
- **AI Processing:** Gemma 4 (via Google Gemini API)
- **Frontend:** Vanilla HTML/JS with custom dark-mode aesthetics
- **Messaging:** Twilio API for WhatsApp

## Local Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your `GEMINI_API_KEY` and `ADMIN_PASSCODE`.
4. Run the server: `python app.py`

## Administration
Admin API routes are secured. You must pass your passcode via the `x-admin-passcode` HTTP Header or the `admin_passcode` query parameter to access the `/api/admin/*` endpoints.
