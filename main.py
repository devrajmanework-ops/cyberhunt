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
    "cybersecurity internship India site:internshala.com OR site:indeed.co.in OR site:linkedin.com",
    "entry level SOC analyst India site:indeed.co.in OR site:naukri.com",
    "ethical hacking fresher job India 2025",
]

SYSTEM_PROMPT = """You are CyberHunt, a strict no-nonsense job search agent.
Search the web for entry-level cybersecurity jobs and internships in India.
Look on Internshala, Indeed India, Naukri, and LinkedIn.
Return ONLY a valid JSON array, no markdown, no explanation, no preamble, nothing else.
Each object must have exactly these keys:
- title: job title
- company: company name
- location: city or Remote
- type: Internship or Full-time
- link: URL (use https://internshala.com/internships/computer-science-internship if no direct link)
- posted: approximate date like "1 week ago" or "March 2025"
Always return at least 3-5 results even if older. Never return empty array.
Example format:
[{"title":"Security Analyst Intern","company":"TCS","location":"Bangalore","type":"Internship","link":"https://internshala.com","posted":"2 weeks ago"}]
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
                    "max_tokens": 1500,
                    "system": SYSTEM_PROMPT,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{
                        "role": "user",
                        "content": f"Search for: {keyword}. Today is {datetime.now().strftime('%B %d, %Y')}. Return ONLY a JSON array, nothing else."
                    }]
                },
                timeout=90
            )
            data = resp.json()
            text = "".join(b["text"] for b in data.get("content", []) if b["type"] == "text")
            text = text.replace("```json", "").replace("```", "").strip()
            start, end = text.find("["), text.rfind("]")
            if start != -1:
                jobs = json.loads(text[start:end+1])
                all_jobs.extend(jobs)
                print(f"Found {len(jobs)} jobs for: {keyword}")
            else:
                print(f"No JSON found for: {keyword}. Response: {text[:200]}")
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
    return unique[:6]


def format_whatsapp_message(jobs):
    if not jobs:
        lines = [
            "*CyberHunt Daily Alert*",
            f"_{datetime.now().strftime('%d %b %Y')}_\n",
            "No new cybersecurity openings found today.",
            "Check manually:",
            "- https://internshala.com/internships/computer-science-internship",
            "- https://in.indeed.com/q-cyber-security-jobs.html",
            "- https://www.naukri.com/cyber-security-jobs",
        ]
        return "\n".join(lines)

    lines = [
        "*CyberHunt Daily Alert*",
        f"_{datetime.now().strftime('%d %b %Y')}_ | {len(jobs)} openings\n"
    ]
    for i, j in enumerate(jobs, 1):
        lines.append(f"*{i}. {j.get('title', 'N/A')}*")
        lines.append(f"   {j.get('company', '?')} — {j.get('location', '?')}")
        lines.append(f"   {j.get('type', '?')} | {j.get('posted', 'Recent')}")
        lines.append(f"   {j.get('link', 'https://internshala.com')}")
        lines.append("")
    lines.append("_CyberHunt | Daily at 9AM IST_")
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
    message = format_whatsapp_message(jobs)
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
