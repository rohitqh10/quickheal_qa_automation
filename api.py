"""
Quick Heal QA Automation - API Server
Exposes the scanner as HTTP endpoints so Activepieces (or any tool) can call it
with a plain HTTP Request piece, without needing to run Python/Playwright itself.

Run:
    python3 -m uvicorn api:app --host 0.0.0.0 --port 8000

Endpoints:
    POST /scan            {"name": "...", "url": "..."}          -> full 12-check result for one site
    POST /ai-summary      {"results": [ ... ]}                    -> AI summary JSON
    POST /generate-report {"results": [...], "ai_summary": {...}} -> HTML report string
    GET  /health                                                  -> {"ok": true}

Deploy this on any small VM / Render / Railway / internal server reachable by
your Activepieces instance, then point the Activepieces HTTP Request pieces at it.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

import runner
import ai_summary as ai_summary_mod
import report as report_mod

app = FastAPI(title="Quick Heal QA Automation API")


class ScanRequest(BaseModel):
    name: str
    url: str


class SummaryRequest(BaseModel):
    results: List[Dict[str, Any]]


class ReportRequest(BaseModel):
    results: List[Dict[str, Any]]
    ai_summary: Dict[str, Any]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/scan")
def scan_site(req: ScanRequest):
    """Runs all 12 QA checks against a single website and returns the result."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            result = runner.run_checks_for_site(req.name, req.url, browser)
        finally:
            browser.close()
    return result


@app.post("/ai-summary")
def ai_summary_endpoint(req: SummaryRequest):
    """Sends aggregated results to the configured AI provider and returns summary + action items."""
    return ai_summary_mod.get_ai_summary(req.results)


@app.post("/generate-report")
def generate_report_endpoint(req: ReportRequest):
    """Builds the final HTML report from results + AI summary."""
    html = report_mod.build_html_report(req.results, req.ai_summary)
    return {"html": html}


class RunAllRequest(BaseModel):
    websites: List[Dict[str, str]] = None


@app.post("/run-daily-qa")
def run_daily_qa(req: RunAllRequest = None):
    """One-call endpoint: scans every website, gets the AI summary, and builds the HTML report.
    Returns: {"results": [...], "ai_summary": {...}, "html": "...", "has_critical": bool}"""
    import config as config_mod
    sites = (req.websites if req and req.websites else config_mod.WEBSITES)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            results = [runner.run_checks_for_site(s["name"], s["url"], browser) for s in sites]
        finally:
            browser.close()

    summary = ai_summary_mod.get_ai_summary(results)
    html = report_mod.build_html_report(results, summary)
    has_critical = any(r.get("overall_status") == "critical" for r in results)

    return {"results": results, "ai_summary": summary, "html": html, "has_critical": has_critical}
