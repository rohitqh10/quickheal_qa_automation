"""
Quick Heal QA Automation - HTML Report Generator
Builds the daily QA health report in the format shown to management.
"""

import datetime

STATUS_LABEL = {
    "healthy": ("&#9989; Healthy", "#1D9E75"),
    "warning": ("&#9888; Warning", "#BA7517"),
    "critical": ("&#10060; Critical", "#A32D2D"),
}


def _status_row(r):
    label, color = STATUS_LABEL.get(r.get("overall_status"), ("Unknown", "#888"))
    notes = []
    if r.get("ssl", {}).get("warning") or r.get("ssl", {}).get("error"):
        notes.append("SSL issue")
    rt = r.get("response_time", {}).get("seconds")
    if rt and rt > 2.0:
        notes.append(f"Slow response ({rt}s)")
    if r.get("broken_links", {}).get("broken"):
        notes.append(f"{len(r['broken_links']['broken'])} broken links")
    note_text = f" &mdash; {', '.join(notes)}" if notes else ""
    return f"""
    <tr>
      <td style="padding:10px;border-bottom:1px solid #eee;">{r.get('name')}</td>
      <td style="padding:10px;border-bottom:1px solid #eee;color:{color};font-weight:600;">{label}{note_text}</td>
    </tr>"""


def build_html_report(results, ai_summary, company="Quick Heal"):
    date_str = datetime.datetime.now().strftime("%d %B %Y")

    total = len(results)
    healthy = sum(1 for r in results if r.get("overall_status") == "healthy")
    failed = sum(1 for r in results if r.get("overall_status") in ("critical", "warning"))
    valid_rt = [r["response_time"]["seconds"] for r in results if r.get("response_time", {}).get("seconds")]
    avg_rt = round(sum(valid_rt) / len(valid_rt), 2) if valid_rt else 0
    ssl_expiring = sum(1 for r in results if r.get("ssl", {}).get("warning"))
    broken_links = sum(len(r.get("broken_links", {}).get("broken", [])) for r in results)
    console_errors = sum(r.get("console_errors", {}).get("count", 0) for r in results)
    forms_failed = sum(1 for r in results if r.get("form_submission", {}).get("ok") is False)
    checkout_failed = sum(1 for r in results if r.get("checkout", {}).get("ok") is False)

    rows = "".join(_status_row(r) for r in results)
    summary_items = "".join(f"<li>{b}</li>" for b in ai_summary.get("summary_bullets", []))
    action_items = "".join(f"<li>{a}</li>" for a in ai_summary.get("action_items", []))

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{company} Daily QA Health Report</title>
</head>
<body style="font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;margin:0;padding:20px;">
  <div style="max-width:680px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #e5e5e5;">
    <div style="background:#0c447c;color:#fff;padding:20px 24px;">
      <h1 style="margin:0;font-size:20px;">{company} Daily QA Health Report</h1>
      <div style="opacity:0.85;font-size:13px;margin-top:4px;">Date: {date_str}</div>
    </div>

    <div style="padding:24px;">
      <h2 style="font-size:16px;margin-top:0;">Website Status</h2>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr>
            <th style="text-align:left;padding:10px;border-bottom:2px solid #ddd;">Website</th>
            <th style="text-align:left;padding:10px;border-bottom:2px solid #ddd;">Status</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>

      <h2 style="font-size:16px;">Performance</h2>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <tr><td style="padding:6px 0;">Websites Checked</td><td style="padding:6px 0;text-align:right;font-weight:600;">{total}</td></tr>
        <tr><td style="padding:6px 0;">Healthy</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#1D9E75;">{healthy}</td></tr>
        <tr><td style="padding:6px 0;">Failed</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#A32D2D;">{failed}</td></tr>
        <tr><td style="padding:6px 0;">Average Response Time</td><td style="padding:6px 0;text-align:right;font-weight:600;">{avg_rt} sec</td></tr>
        <tr><td style="padding:6px 0;">SSL Expiring</td><td style="padding:6px 0;text-align:right;font-weight:600;">{ssl_expiring}</td></tr>
        <tr><td style="padding:6px 0;">Broken Links</td><td style="padding:6px 0;text-align:right;font-weight:600;">{broken_links}</td></tr>
        <tr><td style="padding:6px 0;">Console Errors</td><td style="padding:6px 0;text-align:right;font-weight:600;">{console_errors}</td></tr>
        <tr><td style="padding:6px 0;">Forms Failed</td><td style="padding:6px 0;text-align:right;font-weight:600;">{forms_failed}</td></tr>
        <tr><td style="padding:6px 0;">Checkout Failed</td><td style="padding:6px 0;text-align:right;font-weight:600;">{checkout_failed}</td></tr>
      </table>

      <h2 style="font-size:16px;">AI Summary</h2>
      <ul style="font-size:14px;line-height:1.6;padding-left:20px;">{summary_items}</ul>

      <h2 style="font-size:16px;">Action Items</h2>
      <ul style="font-size:14px;line-height:1.6;padding-left:20px;">{action_items}</ul>
    </div>

    <div style="padding:16px 24px;background:#f9f9f9;font-size:12px;color:#888;border-top:1px solid #eee;">
      Generated automatically by {company} QA Automation &middot; Activepieces workflow
    </div>
  </div>
</body>
</html>"""
    return html
