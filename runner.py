"""
Quick Heal QA Automation - Runner
Runs all 12 checks for a single website and returns a consolidated result dict.
"""

import time
from playwright.sync_api import sync_playwright

import checks
from config import SLOW_RESPONSE_THRESHOLD_SEC


def run_checks_for_site(name, url, browser):
    result = {"name": name, "url": url, "checked_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    # 1. HTTP status (also gives us HTML for downstream checks)
    http = checks.check_http_status(url)
    result["http_status"] = http
    html = http.get("html", "")

    # 2. SSL certificate
    result["ssl"] = checks.check_ssl_certificate(url)

    # 3. Response time
    result["response_time"] = checks.check_response_time(url)

    # 4. Broken links
    result["broken_links"] = checks.check_broken_links(url, html)

    # 5. Sitemap.xml
    result["sitemap"] = checks.check_sitemap(url)

    # 6. robots.txt
    result["robots_txt"] = checks.check_robots_txt(url)

    # 7. Product page validation
    result["product_page"] = checks.check_product_page(html)

    # 8. Checkout page health
    result["checkout"] = checks.check_checkout_page(url)

    # Browser-based checks (9, 10, 11, 12) via Playwright
    console_errors = []
    page = browser.new_page()
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    try:
        page.goto(url, timeout=20000, wait_until="load")
        page.wait_for_timeout(1500)  # let async console errors surface

        # 9. Form submission test
        result["form_submission"] = checks.check_form_submission(page)

        # 10. Console error detection
        result["console_errors"] = {"ok": len(console_errors) == 0, "count": len(console_errors), "errors": console_errors[:10]}

        # 11. Lighthouse-style performance
        result["performance"] = checks.check_lighthouse_style_perf(page)

        # 12. Screenshot capture
        result["screenshot"] = checks.capture_screenshot(page, name)

    except Exception as e:
        result["browser_error"] = str(e)
        result.setdefault("form_submission", {"ok": None, "reason": "page load failed"})
        result.setdefault("console_errors", {"ok": None, "count": 0, "errors": []})
        result.setdefault("performance", {"ok": None})
        result.setdefault("screenshot", {"ok": False})
    finally:
        page.close()

    # --- Overall status classification ---
    result["overall_status"] = classify_status(result)
    return result


def classify_status(r):
    """Returns 'healthy' | 'warning' | 'critical' based on check outcomes."""
    if not r["http_status"].get("ok"):
        return "critical"
    if r["ssl"].get("error") or (r["ssl"].get("warning")):
        return "critical" if r["ssl"].get("error") else "warning"
    if r["response_time"].get("seconds") and r["response_time"]["seconds"] > SLOW_RESPONSE_THRESHOLD_SEC:
        return "warning"
    if r["broken_links"].get("broken"):
        return "warning"
    if r.get("console_errors", {}).get("count", 0) > 5:
        return "warning"
    return "healthy"


def run_all(websites):
    """websites: list of {"name":..., "url":...}. Returns list of result dicts."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for site in websites:
            print(f"Scanning {site['name']} ({site['url']}) ...")
            try:
                r = run_checks_for_site(site["name"], site["url"], browser)
            except Exception as e:
                r = {"name": site["name"], "url": site["url"], "overall_status": "critical", "fatal_error": str(e)}
            results.append(r)
        browser.close()
    return results
