"""
Quick Heal QA Automation - AI Summary
Sends the day's QA results to OpenAI or Groq and asks for a management-style summary.
"""

import json
import requests

from config import AI_PROVIDER, OPENAI_API_KEY, GROQ_API_KEY

SYSTEM_PROMPT = (
    "You are a QA analyst summarizing an automated website health scan for company leadership. "
    "Be concise, factual, and action-oriented. Output STRICT JSON only, no markdown, with this shape: "
    '{"summary_bullets": ["...", "..."], "action_items": ["...", "..."]}. '
    "summary_bullets: 3-5 short factual observations about what changed or what is wrong. "
    "action_items: 3-5 short imperative tasks for the engineering team, ordered by priority."
)


def _build_user_prompt(results):
    compact = []
    for r in results:
        compact.append({
            "name": r.get("name"),
            "status": r.get("overall_status"),
            "http_status": r.get("http_status", {}).get("status_code"),
            "ssl_days_left": r.get("ssl", {}).get("days_left"),
            "response_time_sec": r.get("response_time", {}).get("seconds"),
            "broken_links": len(r.get("broken_links", {}).get("broken", [])),
            "console_errors": r.get("console_errors", {}).get("count"),
            "form_ok": r.get("form_submission", {}).get("ok"),
        })
    return "Today's QA scan results:\n" + json.dumps(compact, indent=2)


def get_ai_summary(results):
    """Returns dict: {"summary_bullets": [...], "action_items": [...]}
    Falls back to a rule-based summary if no API key is configured or the call fails."""
    prompt = _build_user_prompt(results)

    try:
        if AI_PROVIDER == "groq" and GROQ_API_KEY:
            return _call_groq(prompt)
        elif OPENAI_API_KEY:
            return _call_openai(prompt)
    except Exception as e:
        print(f"AI summary call failed, falling back to rule-based summary: {e}")

    return _fallback_summary(results)


def _call_openai(user_prompt):
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    return json.loads(text)


def _call_groq(user_prompt):
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def _fallback_summary(results):
    """Rule-based summary used when no AI key is set, so the pipeline never breaks."""
    bullets, actions = [], []
    for r in results:
        name = r.get("name")
        ssl = r.get("ssl", {})
        if ssl.get("error"):
            bullets.append(f"{name}: SSL certificate check failed.")
            actions.append(f"Fix {name} SSL certificate immediately.")
        elif ssl.get("warning"):
            bullets.append(f"{name}: SSL certificate expires in {ssl.get('days_left')} days.")
            actions.append(f"Renew {name} SSL certificate.")

        rt = r.get("response_time", {}).get("seconds")
        if rt and rt > 2.0:
            bullets.append(f"{name}: slow response time ({rt}s).")
            actions.append(f"Investigate {name} performance.")

        broken = len(r.get("broken_links", {}).get("broken", []))
        if broken:
            bullets.append(f"{name}: {broken} broken link(s) detected.")
            actions.append(f"Resolve broken URLs on {name}.")

        if r.get("form_submission", {}).get("ok") is False:
            bullets.append(f"{name}: form submission check failed.")
            actions.append(f"Verify contact form API on {name}.")

    if not bullets:
        bullets = ["All monitored websites are healthy with no critical issues detected today."]
    if not actions:
        actions = ["No action required today."]

    return {"summary_bullets": bullets[:5], "action_items": actions[:5]}
