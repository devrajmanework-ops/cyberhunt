import os
import json
import time
import schedule
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN  = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM        = os.environ["TWILIO_FROM"]
TWILIO_TO          = os.environ["TWILIO_TO"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]

SEARCH_KEYWORDS = [
    "entry level cybersecurity internship India",
    "SOC analyst fresher India",
    "ethical hacking internship India",
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
    print(f"[{datetime.now()}] Searching for jobs...")
    all_jobs = []
    for keyword in SEARCH_KEYWORDS[:2]:
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
            time.sleep(3)
        except Exception as e:
            print(f"Search error for '{keyword}': {e}")

    seen = set()
    unique = []
    for j in all_jobs:
        key = (j.get("title","").lower(), j.get("company","").lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique[:5]


def format_whatsapp_message(jobs):
    if not jobs:
        return None
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
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    msg = client.messages.create(
        from_=TWILIO_FROM,
        to=TWILIO_TO,
        body=message
    )
    print(f"[{datetime.now()}] WhatsApp sent: {msg.sid}")


def run_daily_alert():
    print(f"[{datetime.now()}] Running daily alert...")
    jobs = search_jobs()
    if not jobs:
        print("No new jobs found today. Skipping alert.")
        return
    message = format_whatsapp_message(jobs)
    if message:
        send_whatsapp(message)
        print(f"[{datetime.now()}] Alert sent with {len(jobs)} jobs.")


def run_scheduler():
    schedule.every().day.at("03:30").do(run_daily_alert)
    run_daily_alert()
    while True:
        schedule.run_pending()
        time.sleep(60)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"CyberHunt running")
    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("CyberHunt Agent started.")
    threading.Thread(target=run_scheduler, daemon=True).start()
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()
