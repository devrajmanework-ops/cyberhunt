# CyberHunt — WhatsApp Job Alert Agent

Sends you daily WhatsApp alerts for entry-level cybersecurity jobs in India.
Fully free. Runs 24/7 on Render.

---

## Step 1 — Set up Twilio (5 mins)

1. Go to https://twilio.com → Sign up (free)
2. In the dashboard, go to: Messaging → Try it → Send a WhatsApp message
3. You'll see a sandbox number like `+1 415 523 8886`
4. On your phone, send this WhatsApp message to that number:
   `join <your-sandbox-keyword>`
   (Twilio shows you the exact keyword — e.g. "join bright-monkey")
5. Note down:
   - Account SID  (from dashboard homepage)
   - Auth Token   (from dashboard homepage)
   - From number  → format: `whatsapp:+14155238886`
   - Your number  → format: `whatsapp:+919876543210`

---

## Step 2 — Get your Anthropic API key (2 mins)

1. Go to https://console.anthropic.com
2. Sign up / log in → API Keys → Create key
3. Copy the key (starts with `sk-ant-...`)

---

## Step 3 — Push code to GitHub

1. Create a new GitHub repo called `cyberhunt`
2. Upload these 3 files:
   - main.py
   - requirements.txt
   - render.yaml

Or use terminal:
```bash
git init
git add .
git commit -m "init"
gh repo create cyberhunt --public --push
```

---

## Step 4 — Deploy on Render (3 mins)

1. Go to https://render.com → Sign up with GitHub
2. Click "New +" → "Blueprint"
3. Connect your `cyberhunt` GitHub repo
4. Render detects `render.yaml` automatically
5. Add your environment variables:

| Key | Value |
|-----|-------|
| TWILIO_ACCOUNT_SID | ACxxxxxxxxxxxxxxxx |
| TWILIO_AUTH_TOKEN | your_auth_token |
| TWILIO_FROM | whatsapp:+14155238886 |
| TWILIO_TO | whatsapp:+91XXXXXXXXXX |
| ANTHROPIC_API_KEY | sk-ant-... |

6. Click "Apply" → Deploy starts

---

## Step 5 — Verify it works

- Check Render logs — you should see "CyberHunt Agent started"
- Within 2 minutes you'll get your first WhatsApp alert
- After that, alerts arrive every day at 9:00 AM IST

---

## Customize

In `main.py`, edit `SEARCH_KEYWORDS` to change what jobs you get.
Change `"03:30"` (UTC) to adjust the alert time.

---

## Troubleshooting

- No WhatsApp received? Check Render logs for errors
- Twilio error 63007? Re-send the join message from your phone
- API error? Check your Anthropic key has credits
