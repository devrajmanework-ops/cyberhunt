import os
import json
import time
import schedule
import requests
from datetime import datetime
from twilio.rest import Client

# ── Config (set these as environment variables in Render) ──────────────────
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM        = os.environ["TWILIO_FROM"]   # e.g. whatsapp:+14155238886
TWILIO_TO          = os.environ["TWILIO_TO"]     # e.g. whatsapp:+919876543210
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]

# ── Job search keywords (customize freely) ─────────────────────────────────
SEARCH_KEYWORDS = [
    "entry level cybersecurity internship India",
    "SOC analyst fresher India",
    "ethical hacking internship India",
    "cybersecurity graduate trainee India",
    "network security internship India",
]

SYSTEM_PROMPT = """You are CyberHunt, a strict job search agent.
Search the web for REAL, CURRENT (last 7 days) entry-level cybersecurity jobs
and internships in India. Return ONLY a JSON array, no markdown, no preamble.
Each object must have:
- title: job title
- company: company name
- location: city or Remote
- type: Internship | Full-time
- link: direct application URL
- posted: when posted (e.g. "2 days ago")
Return 3-5 best matches only. If none found in last 7 days, return empty array [].
"""

def search_jobs():
    """Call Claude with web search to find fresh cybersecurity jobs."""
    print(f"[{datetime.now()}] Searching for jobs...")
    all_jobs = []

    for keyword in SEARCH_KEYWORDS[:2]:  # limit to 2 searches per run
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "system": SYSTEM_PROMPT,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{
                        "role": "user",
                        "content": f"Find jobs for: {keyword}. Today is {datetime.now().strftime('%B %d, %Y')}. Return JSON array only."
                    }]
                },
                timeout=60
            )
            data = resp.json()
            text = "".join(b["text"] for b in data.get("content", []) if b["type"] == "text")
            text = text.replace("```json", "").replace("```", "").strip()
            start, end = text.find("["), text.rfind("]")
            if start != -1:
                jobs = json.loads(text[start:end+1])
                all_jobs.extend(jobs)
            time.sleep(3)  # be polite between requests
        except Exception as e:
            print(f"Search error for '{keyword}': {e}")

    # Deduplicate by title+company
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j.get("title","").lower(), j.get("company","").lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)

    return unique[:5]  # max 5 per alert


def format_whatsapp_message(jobs):
    """Format jobs into a clean WhatsApp message."""
    if not jobs:
        return None  # don't send if nothing found

    lines = [
        "*CyberHunt Daily Alert*",
        f"_{datetime.now().strftime('%d %b %Y')}_ | {len(jobs)} new openings\n"
    ]

    for i, j in enumerate(jobs, 1):
        lines.append(f"*{i}. {j.get('title', 'N/A')}*")
        lines.append(f"   {j.get('company', '?')} — {j.get('location', '?')}")
        lines.append(f"   Type: {j.get('type', '?')} | Posted: {j.get('posted', 'Recent')}")
        lines.append(f"   Apply: {j.get('link', 'Search on LinkedIn')}")
        lines.append("")

    lines.append("_Reply STOP to unsubscribe_")
    return "\n".join(lines)


def send_whatsapp(message):
    """Send message via Twilio WhatsApp."""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        from_=TWILIO_FROM,
        to=TWILIO_TO,
        body=message
    )
    print(f"[{datetime.now()}] WhatsApp sent: {msg.sid}")


def run_daily_alert():
    """Main job: search + send."""
    print(f"[{datetime.now()}] Running daily alert...")
    jobs = search_jobs()
    if not jobs:
        print("No new jobs found today. Skipping alert.")
        return
    message = format_whatsapp_message(jobs)
    if message:
        send_whatsapp(message)
        print(f"[{datetime.now()}] Alert sent with {len(jobs)} jobs.")


# ── Schedule: run once a day at 9:00 AM IST (3:30 AM UTC) ─────────────────
schedule.every().day.at("03:30").do(run_daily_alert)

if __name__ == "__main__":
    print("CyberHunt Agent started. Waiting for scheduled run...")
    run_daily_alert()  # run once immediately on startup
    while True:
        schedule.run_pending()
        time.sleep(60)
