#!/usr/bin/env python3
"""
GuruShots boost-availability checker.

Logs into GuruShots via its (unofficial) web API, checks all your
active challenges, and sends a push notification via ntfy.sh whenever
a "boost" becomes available on one of them.

GuruShots' API blocks plain HTTP clients (curl, Python requests) via
TLS/browser fingerprinting even with correct credentials and matching
headers - it silently returns "Email or password is incorrect" instead
of an explicit bot-check error. curl_cffi is used instead of requests
because it can impersonate a real Chrome TLS fingerprint.

Credentials and the ntfy topic are read from environment variables so
they never end up hardcoded in the file:

    GURUSHOTS_EMAIL      your GuruShots login email
    GURUSHOTS_PASSWORD   your GuruShots password
    NTFY_TOPIC           a hard-to-guess topic name, e.g. "kj-gurushots-9f2a"

Install dependency:
    pip install curl_cffi

Run manually:
    GURUSHOTS_EMAIL=... GURUSHOTS_PASSWORD=... NTFY_TOPIC=... python3 gurushots_boost_check.py
"""

import os
import sys
from curl_cffi import requests
from curl_cffi.requests.exceptions import RequestException

API_BASE = "https://api.gurushots.com/rest"

HEADERS_BASE = {
    "accept": "application/json, text/plain, */*",
    "x-requested-with": "XMLHttpRequest",
    "x-api-version": "13",
    "x-env": "WEB",
    "origin": "https://gurushots.com",
    "referer": "https://gurushots.com/",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US;q=1.0",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
}


def login(email: str, password: str) -> dict:
    """Logs in and returns the parsed JSON response, which includes a token."""
    headers = {
        **HEADERS_BASE,
        "content-type": "application/x-www-form-urlencoded",
    }
    resp = requests.post(
        f"{API_BASE}/signin",
        headers=headers,
        data={"login": email, "password": password},
        impersonate="chrome124",
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_active_challenges(token: str) -> dict:
    headers = {**HEADERS_BASE, "x-token": token}
    resp = requests.post(
        f"{API_BASE}/get_my_active_challenges",
        headers=headers,
        impersonate="chrome124",
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def notify(topic: str, title: str, message: str) -> None:
    requests.post(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "high", "Tags": "camera_flash"},
        timeout=10,
    )


def main() -> int:
    email = os.environ.get("GURUSHOTS_EMAIL")
    password = os.environ.get("GURUSHOTS_PASSWORD")
    ntfy_topic = os.environ.get("NTFY_TOPIC")

    missing = [
        name
        for name, val in [
            ("GURUSHOTS_EMAIL", email),
            ("GURUSHOTS_PASSWORD", password),
            ("NTFY_TOPIC", ntfy_topic),
        ]
        if not val
    ]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        return 1

    try:
        login_data = login(email, password)
    except RequestException as e:
        print(f"Login request failed: {e}")
        return 1

    token = login_data.get("token")
    if not token:
        print(f"Login did not return a token. Response: {login_data}")
        return 1

    try:
        data = get_active_challenges(token)
    except RequestException as e:
        print(f"Fetching active challenges failed: {e}")
        return 1

    challenges = data.get("challenges", [])
    if not challenges:
        print("No active challenges found.")
        return 0

    found_any = False
    for challenge in challenges:
        title = challenge.get("title", "Unknown challenge")
        boost = challenge.get("member", {}).get("boost", {})
        state = boost.get("state")
        print(f"- {title}: boost state = {state}")

        if state == "AVAILABLE":
            found_any = True
            notify(
                ntfy_topic,
                "GuruShots boost available!",
                f"Your free boost is ready for: {title}",
            )

    if not found_any:
        print("No boosts available right now.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
