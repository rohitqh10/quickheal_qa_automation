"""
Quick Heal QA Automation - Integrations
Google Sheets (read website list), Gmail (send report), Microsoft Teams (webhook alert).
All optional - script runs fine without any of these configured.
"""

import csv
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import (
    GOOGLE_SHEET_CSV_URL, WEBSITES,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO,
    TEAMS_WEBHOOK_URL,
)


def load_website_list():
    """Reads from a published Google Sheet CSV if configured, else uses the WEBSITES list in config.py."""
    if not GOOGLE_SHEET_CSV_URL:
        return WEBSITES
    try:
        resp = requests.get(GOOGLE_SHEET_CSV_URL, timeout=15)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        sites = [{"name": row["name"], "url": row["url"]} for row in reader if row.get("url")]
        return sites if sites else WEBSITES
    except Exception as e:
        print(f"Could not load Google Sheet ({e}), falling back to config.py list.")
        return WEBSITES


def send_email_report(html_report, subject=None):
    """Sends the HTML report via SMTP (e.g. Gmail with an app password)."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("Email not configured (SMTP_* / QA_EMAIL_TO env vars missing) - skipping send.")
        return False

    subject = subject or "Quick Heal Daily QA Health Report"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(html_report, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_TO.split(","), msg.as_string())
    print(f"Email sent to {EMAIL_TO}")
    return True


def send_teams_alert(results):
    """Posts a critical-issue alert to a Microsoft Teams channel via Incoming Webhook."""
    if not TEAMS_WEBHOOK_URL:
        print("Teams webhook not configured (QA_TEAMS_WEBHOOK_URL) - skipping alert.")
        return False

    critical = [r for r in results if r.get("overall_status") == "critical"]
    if not critical:
        print("No critical issues - Teams alert not needed.")
        return False

    lines = [f"- **{r['name']}**: {r.get('http_status', {}).get('status_code', 'error')}" for r in critical]
    card = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "A32D2D",
        "summary": "Quick Heal QA Critical Alert",
        "title": "Critical QA issue detected",
        "text": "\n\n".join(lines),
    }
    resp = requests.post(TEAMS_WEBHOOK_URL, json=card, timeout=15)
    resp.raise_for_status()
    print("Teams alert sent.")
    return True
