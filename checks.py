"""
Quick Heal QA Automation - Check functions
Each function returns a dict of results for one website.
"""

import os
import ssl
import socket
import time
import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import (
    REQUEST_TIMEOUT_SEC,
    SLOW_RESPONSE_THRESHOLD_SEC,
    SSL_EXPIRY_WARNING_DAYS,
    MAX_LINKS_TO_CHECK_PER_SITE,
    SCREENSHOT_DIR,
)

HEADERS = {"User-Agent": "QuickHealQABot/1.0 (+internal QA automation)"}


def check_http_status(url):
    """1. HTTP Status Check"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SEC, allow_redirects=True)
        return {"ok": r.status_code < 400, "status_code": r.status_code, "final_url": r.url, "html": r.text}
    except requests.RequestException as e:
        return {"ok": False, "status_code": None, "error": str(e), "html": ""}


def check_ssl_certificate(url):
    """2. SSL Certificate Check - returns days until expiry"""
    host = urlparse(url).hostname
    if not host:
        return {"ok": False, "error": "invalid host"}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=REQUEST_TIMEOUT_SEC) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        expiry = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (expiry - datetime.datetime.utcnow()).days
        return {
            "ok": days_left > SSL_EXPIRY_WARNING_DAYS,
            "days_left": days_left,
            "expires": expiry.strftime("%Y-%m-%d"),
            "warning": days_left <= SSL_EXPIRY_WARNING_DAYS,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "days_left": None}


def check_response_time(url):
    """3. Response Time"""
    try:
        start = time.time()
        requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SEC)
        elapsed = round(time.time() - start, 2)
        return {"ok": elapsed < SLOW_RESPONSE_THRESHOLD_SEC, "seconds": elapsed}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e), "seconds": None}


def check_broken_links(url, html, max_links=MAX_LINKS_TO_CHECK_PER_SITE):
    """4. Broken Links - checks internal links found on the page"""
    if not html:
        return {"ok": False, "broken": [], "checked": 0}
    soup = BeautifulSoup(html, "html.parser")
    base = urlparse(url)
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(url, href)
        if urlparse(full).netloc == base.netloc:
            links.add(full)
        if len(links) >= max_links:
            break

    broken = []
    for link in links:
        try:
            r = requests.head(link, headers=HEADERS, timeout=8, allow_redirects=True)
            if r.status_code >= 400:
                # HEAD sometimes unsupported, retry with GET
                r = requests.get(link, headers=HEADERS, timeout=8)
            if r.status_code >= 400:
                broken.append({"url": link, "status": r.status_code})
        except requests.RequestException as e:
            broken.append({"url": link, "status": "error", "error": str(e)})

    return {"ok": len(broken) == 0, "broken": broken, "checked": len(links)}


def check_sitemap(url):
    """5. Sitemap.xml Check"""
    sitemap_url = urljoin(url, "/sitemap.xml")
    try:
        r = requests.get(sitemap_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SEC)
        ok = r.status_code == 200 and ("<urlset" in r.text or "<sitemapindex" in r.text)
        return {"ok": ok, "status_code": r.status_code, "url": sitemap_url}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e), "url": sitemap_url}


def check_robots_txt(url):
    """6. robots.txt Check"""
    robots_url = urljoin(url, "/robots.txt")
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SEC)
        ok = r.status_code == 200 and "user-agent" in r.text.lower()
        return {"ok": ok, "status_code": r.status_code, "url": robots_url}
    except requests.RequestException as e:
        return {"ok": False, "error": str(e), "url": robots_url}


def check_product_page(html):
    """7. Product Page Validation - heuristic check for product/pricing indicators"""
    if not html:
        return {"ok": False, "reason": "no html"}
    lower = html.lower()
    signals = ["add to cart", "buy now", "price", "product", "subscribe", "download"]
    found = [s for s in signals if s in lower]
    return {"ok": len(found) >= 2, "signals_found": found}


def check_checkout_page(url):
    """8. Checkout Page Health - tries common checkout/cart paths"""
    candidates = ["/checkout", "/cart", "/buy", "/purchase"]
    for path in candidates:
        try:
            full = urljoin(url, path)
            r = requests.get(full, headers=HEADERS, timeout=8)
            if r.status_code < 400:
                return {"ok": True, "url": full, "status_code": r.status_code}
        except requests.RequestException:
            continue
    return {"ok": None, "reason": "no standard checkout path found (may need site-specific URL)"}


def check_form_submission(page):
    """9. Form Submission Test - uses an already-open Playwright page.
    Finds the first form and checks it has actionable inputs (non-destructive: does not submit)."""
    try:
        forms = page.query_selector_all("form")
        if not forms:
            return {"ok": None, "reason": "no form found on page"}
        first = forms[0]
        inputs = first.query_selector_all("input, textarea, select")
        has_submit = first.query_selector("button[type=submit], input[type=submit], button") is not None
        return {"ok": len(inputs) > 0 and has_submit, "forms_found": len(forms), "inputs_found": len(inputs)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def check_console_errors(page):
    """10. Console Error Detection - collected via Playwright page listener (see runner.py)"""
    # populated externally by the runner via page.on("console", ...)
    return {}


def check_lighthouse_style_perf(page):
    """11. Lighthouse-style Performance - uses Navigation Timing API via JS eval (lightweight proxy, no full Lighthouse)"""
    try:
        timing = page.evaluate("""() => {
            const nav = performance.getEntriesByType('navigation')[0];
            if (!nav) return null;
            return {
                dom_content_loaded_ms: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
                load_event_ms: Math.round(nav.loadEventEnd - nav.startTime),
                ttfb_ms: Math.round(nav.responseStart - nav.startTime),
                transfer_size_kb: Math.round((nav.transferSize || 0) / 1024)
            };
        }""")
        return {"ok": timing is not None, "metrics": timing}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def capture_screenshot(page, name, out_dir=SCREENSHOT_DIR):
    """12. Screenshot Capture"""
    os.makedirs(out_dir, exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in name)
    path = os.path.join(out_dir, f"{safe_name}.png")
    try:
        page.screenshot(path=path, full_page=False)
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": str(e)}
