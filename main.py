"""
Quick Heal QA Automation - Main
Run with:  python3 main.py

Env vars you can set before running:
  OPENAI_API_KEY=sk-...          (or GROQ_API_KEY=gsk-...  with QA_AI_PROVIDER=groq)
  QA_SHEET_CSV_URL=https://...   (optional, published Google Sheet CSV)
  QA_SMTP_USER / QA_SMTP_PASS / QA_EMAIL_TO   (optional, to actually send email)
  QA_TEAMS_WEBHOOK_URL           (optional, to actually post to Teams)
"""

import json
import os

from config import OUTPUT_DIR
from runner import run_all
from ai_summary import get_ai_summary
from report import build_html_report
from integrations import load_website_list, send_email_report, send_teams_alert


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("Quick Heal QA Daily Automation")
    print("=" * 60)

    websites = load_website_list()
    print(f"Loaded {len(websites)} websites to scan.\n")

    results = run_all(websites)

    raw_path = os.path.join(OUTPUT_DIR, "raw_results.json")
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nRaw results saved to {raw_path}")

    print("\nGenerating AI summary...")
    ai_summary = get_ai_summary(results)

    print("Building HTML report...")
    html_report = build_html_report(results, ai_summary)
    report_path = os.path.join(OUTPUT_DIR, "daily_qa_report.html")
    with open(report_path, "w") as f:
        f.write(html_report)
    print(f"HTML report saved to {report_path}")

    send_email_report(html_report)
    send_teams_alert(results)

    print("\nSummary:")
    for r in results:
        print(f"  {r['name']:<25} {r.get('overall_status', 'unknown').upper()}")

    print("\nDone. Open the HTML report to view the full result:")
    print(f"  {os.path.abspath(report_path)}")


if __name__ == "__main__":
    main()
