"""
Quick Heal QA Automation - Configuration
Edit WEBSITES below, or point GOOGLE_SHEET_CSV_URL at a published Google Sheet CSV
(File > Share > Publish to web > CSV) to pull the list dynamically.
"""

import os

# --- Website list (fallback if no Google Sheet is configured) ---
WEBSITES = [
    {"name": "Seqrite", "url": "https://www.seqrite.com/"},
    {"name": "Quick Heal Foundation", "url": "https://www.quickhealfoundation.org/"},
    {"name": "Guardian (Dev/Staging)", "url": "https://devstg.quickheal.co.in/guardian/"},
    {"name": "Guardian AV", "url": "https://www.guardianav.co.in/"},
    {"name": "Quick Heal QA OCI (India)", "url": "https://qaoci.quickheal.co.in/"},
    {"name": "Quick Heal India", "url": "https://www.quickheal.co.in/"},
    {"name": "Quick Heal QA OCI (Global)", "url": "https://qaoci.quickheal.com/"},
    {"name": "Quick Heal Global", "url": "https://www.quickheal.com/"},
    {"name": "Quick Heal US QA OCI", "url": "https://usqaoci.quickheal.com/"},
    {"name": "Quick Heal US", "url": "https://us.quickheal.com/"},
    {"name": "Quick Heal Academy (Preprod)", "url": "https://preprod.quickhealacademy.com/"},
    {"name": "Quick Heal Academy", "url": "https://www.quickhealacademy.com/"},
    {"name": "Quick Heal Japan", "url": "https://www.quickheal.co.jp/"},
    {"name": "Seqrite Japan", "url": "https://www.seqrite.jp/"},
    {"name": "Quick Heal Blogs (QA OCI)", "url": "https://qaoci.quickheal.com/blogs/"},
    {"name": "Quick Heal Blogs", "url": "https://www.quickheal.com/blogs/"},
    {"name": "Quick Heal Knowledge Centre", "url": "https://www.quickheal.co.in/knowledge-centre/"},
    {"name": "Quick Heal US Blogs", "url": "https://us.quickheal.com/blogs/"},
    {"name": "Quick Heal Docs", "url": "https://docs.quickheal.com/"},
    {"name": "Seqrite Docs", "url": "https://docs.seqrite.com/"},
    {"name": "Cybisec", "url": "https://www.cybisec.com/"},
]

# --- Optional: pull the list live from Google Sheets instead ---
# Publish your sheet as CSV (File > Share > Publish to web > CSV) and paste the link here.
GOOGLE_SHEET_CSV_URL = os.environ.get("QA_SHEET_CSV_URL", "")

# --- AI Summary provider ---
# Set one of these as an environment variable before running:
#   export OPENAI_API_KEY="sk-..."
#   export GROQ_API_KEY="gsk_..."
AI_PROVIDER = os.environ.get("QA_AI_PROVIDER", "groq")  # "openai" or "groq"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# --- Thresholds ---
SLOW_RESPONSE_THRESHOLD_SEC = 2.0
SSL_EXPIRY_WARNING_DAYS = 30
REQUEST_TIMEOUT_SEC = 15
MAX_LINKS_TO_CHECK_PER_SITE = 25  # keep runtime sane; raise for full crawl

# --- Output ---
OUTPUT_DIR = os.environ.get("QA_OUTPUT_DIR", "./qa_reports")
SCREENSHOT_DIR = os.path.join(OUTPUT_DIR, "screenshots")

# --- Email (optional, for direct SMTP sending instead of Activepieces/Gmail) ---
SMTP_HOST = os.environ.get("QA_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("QA_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("QA_SMTP_USER", "")
SMTP_PASS = os.environ.get("QA_SMTP_PASS", "")
EMAIL_TO = os.environ.get("QA_EMAIL_TO", "")

# --- Microsoft Teams (optional, Incoming Webhook URL) ---
TEAMS_WEBHOOK_URL = os.environ.get("QA_TEAMS_WEBHOOK_URL", "")
