# 📲 Sentry Live WhatsApp Chatbot Integration Guide

This guide details step-by-step instructions for deploying Sentry live and connecting it to official WhatsApp messaging channels (**Meta WhatsApp Business Cloud API** or **Twilio for WhatsApp**).

---

## 🛠️ Method A: Official Meta WhatsApp Business Cloud API (Recommended)

### Step 1: Create a Meta Developer Account & WhatsApp App
1. Go to [developers.facebook.com](https://developers.facebook.com/) and sign in.
2. Click **My Apps** > **Create App**.
3. Choose **Other** > Select **Business** as app type.
4. Name your app (e.g. `Sentry-KWASU-Intelligence`) and click **Create App**.
5. Under "Add products to your app", click **Set up** on **WhatsApp**.

### Step 2: Get API Keys & Phone Number ID
1. In the left navigation, go to **WhatsApp > API Setup**.
2. Copy the following credentials:
   - **Temporary / Permanent Access Token**
   - **Phone Number ID** (e.g. `100234567890123`)
   - Test Phone Number (or register KWASU's official WhatsApp Business number).

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` on your deployment server:

```bash
cp .env.example .env
```

Set the values in `.env`:
```ini
WHATSAPP_PROVIDER=meta
META_WA_PHONE_NUMBER_ID=100234567890123
META_WA_ACCESS_TOKEN=EAAG...your_long_lived_token...
META_WA_VERIFY_TOKEN=sentry_kwasu_secret_2026
GROQ_API_KEY=gsk_...your_groq_gemma_key...
```

### Step 4: Configure Webhook in Meta Dashboard
1. Deploy your server so it has a public HTTPS URL (e.g. `https://sentry.kwasu.edu.ng` or via ngrok for testing `https://xxxx.ngrok-free.app`).
2. In Meta App Dashboard, go to **WhatsApp > Configuration**.
3. Under **Webhook**, click **Edit**.
4. Enter:
   - **Callback URL:** `https://your-domain.com/webhook/whatsapp`
   - **Verify Token:** `sentry_kwasu_secret_2026` (matching `META_WA_VERIFY_TOKEN` in `.env`).
5. Click **Verify and Save**.
6. Under **Webhook Fields**, click **Subscribe** for `messages`.

---

## 📞 Method B: Twilio for WhatsApp API

### Step 1: Set Up Twilio Sandbox or WhatsApp Business Number
1. Sign in to [Twilio Console](https://www.twilio.com/console).
2. Navigate to **Messaging > Try it out > Send a WhatsApp message** to activate Twilio Sandbox.
3. Copy your **Account SID** and **Auth Token**.

### Step 2: Configure Environment Variables
Set your `.env`:
```ini
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=AC...your_account_sid...
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WA_PHONE_NUMBER=whatsapp:+14155238886
```

### Step 3: Set Twilio Webhook URL
1. In Twilio Console, go to **Messaging > Settings > WhatsApp Sandbox Settings**.
2. Under "WHEN A MESSAGE COMES IN", set URL to:
   `https://your-domain.com/webhook/twilio`
3. Method: `HTTP POST`.
4. Click **Save**.

---

## 🚀 Live Deployment Instructions (Railway / Render / DigitalOcean / AWS)

### Option 1: One-Click Deploy on Railway or Render
1. Push this workspace codebase to a private/public GitHub repository.
2. On Railway/Render, create a new **Web Service** linked to your repository.
3. Set the Build Command: `pip install -r requirements.txt` (or pip install fastapi uvicorn sqlite-utils requests pydantic).
4. Set Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`.

### Option 2: VPS / Ubuntu Server Deployment (Nginx + Systemd + SSL)

1. **Install Dependencies on Server:**
```bash
sudo apt update && sudo apt install -y python3-pip nginx certbot python3-certbot-nginx
```

2. **Clone Code & Create Virtualenv:**
```bash
git clone https://github.com/your-org/sentry-kwasu.git /opt/sentry
cd /opt/sentry
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn requests pydantic python-multipart
```

3. **Create Systemd Service (`/etc/systemd/system/sentry.service`):**
```ini
[Unit]
Description=Sentry Gemma 4 WhatsApp Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/sentry
ExecStart=/opt/sentry/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Enable & Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sentry
```

5. **Setup Nginx Proxy with Free SSL Certbot:**
```nginx
server {
    server_name sentry.kwasu.edu.ng;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo certbot --nginx -d sentry.kwasu.edu.ng
```

Your live Sentry software backend is now operational over SSL HTTPS, handling live WhatsApp incoming webhooks 24/7!
