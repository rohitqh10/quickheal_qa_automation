# Quick Heal QA Automation - Setup

## 1. Install (one-time, on the server that will run this)
    pip install -r requirements.txt
    playwright install --with-deps chromium

## 2. Run the demo/report locally
    export GROQ_API_KEY="gsk_..."
    export QA_AI_PROVIDER="groq"
    python3 main.py
    # -> qa_reports/daily_qa_report.html

## 3. Run as an API for Activepieces
    export GROQ_API_KEY="gsk_..."
    export QA_AI_PROVIDER="groq"
    python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
    # Then point Activepieces HTTP Request pieces at http://<your-server>:8000

## 4. Config
Edit config.py or set environment variables:
    GROQ_API_KEY (default provider) / OPENAI_API_KEY   - AI summary
    QA_AI_PROVIDER                  - "groq" (default) or "openai"
    QA_SHEET_CSV_URL                - published Google Sheet CSV (site list)
    QA_SMTP_USER / QA_SMTP_PASS / QA_EMAIL_TO   - direct email (optional, Activepieces Gmail piece is the primary path)
    QA_TEAMS_WEBHOOK_URL            - Microsoft Teams Incoming Webhook (optional, Activepieces Teams piece is the primary path)
