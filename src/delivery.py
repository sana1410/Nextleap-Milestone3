import json
import os
import re

import requests as http_requests

from config import (
    GOOGLE_DOC_ID,
    EMAIL_RECIPIENT,
    MCP_SERVER_URL,
    PULSE_PATH,
    DATA_DIR,
)

FALLBACK_PATH = os.path.join(DATA_DIR, "pulse_fallback.md")


class MCPClient:
    """Minimal MCP client for Streamable HTTP transport."""

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/mcp"
        self.session_id = None
        self._request_id = 0

    def _next_id(self):
        self._request_id += 1
        return self._request_id

    def _post(self, payload):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        resp = http_requests.post(
            self.endpoint,
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()

        if "mcp-session-id" in resp.headers:
            self.session_id = resp.headers["mcp-session-id"]

        body = resp.text.strip()
        if not body:
            return None

        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            return self._parse_sse(body)
        return resp.json()

    def _parse_sse(self, text):
        result = None
        for line in text.split("\n"):
            if line.startswith("data: "):
                try:
                    result = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass
        return result

    def initialize(self):
        init_result = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "groww-pulse-delivery", "version": "1.0.0"},
            },
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return init_result

    def call_tool(self, name, arguments=None):
        response = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {},
            },
        })

        if response is None:
            raise Exception(f"Empty response from MCP server for tool '{name}'")

        if "error" in response:
            err = response["error"]
            raise Exception(
                f"MCP error ({err.get('code', '?')}): {err.get('message', str(err))}"
            )

        result = response.get("result", {})
        if result.get("isError"):
            content = result.get("content", [])
            msg = next((b["text"] for b in content if b.get("type") == "text"), str(result))
            raise Exception(f"Tool '{name}' failed: {msg}")

        content = result.get("content", [])
        texts = [b["text"] for b in content if b.get("type") == "text"]
        return "\n".join(texts) if texts else json.dumps(result)


def check_auth(client):
    print("Checking MCP server authentication...")
    raw = client.call_tool("auth_status")
    status = json.loads(raw)

    authenticated = status.get("authenticated", False)
    scopes = status.get("scopes", [])

    print(f"  Authenticated: {authenticated}")
    print(f"  Scopes: {', '.join(scopes)}")

    if not authenticated:
        raise Exception("MCP server not authenticated with Google. Run auth flow first.")

    has_docs = any("documents" in s for s in scopes)
    has_gmail = any("gmail" in s for s in scopes)
    if not has_docs:
        print("  WARNING: Google Docs scope not granted")
    if not has_gmail:
        print("  WARNING: Gmail scope not granted")

    return status


def publish_to_docs(client, pulse_text, title, doc_id=None, dry_run=False):
    doc_id = doc_id or GOOGLE_DOC_ID
    if not doc_id:
        raise ValueError("GOOGLE_DOC_ID not configured. Set it in .env")

    print(f"{'[DRY RUN] ' if dry_run else ''}Publishing pulse to Google Doc...")
    print(f"  Document ID: {doc_id}")

    result_raw = client.call_tool("gdocs_append_text", {
        "document_id": doc_id,
        "text": pulse_text,
        "add_heading": title,
        "add_timestamp": True,
        "separator": "horizontal_rule",
        "dry_run": dry_run,
    })

    print(f"  Result: {result_raw[:200]}")

    try:
        result_data = json.loads(result_raw)
        if "error" in result_data:
            raise Exception(
                f"Google Docs error: {result_data['error']} "
                f"({result_data.get('hint', '')})"
            )
    except json.JSONDecodeError:
        pass

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"  Doc URL: {doc_url}")
    return doc_url


def send_pulse_email(client, pulse_text, doc_url, recipient=None, dry_run=False):
    recipient = recipient or EMAIL_RECIPIENT
    if not recipient:
        raise ValueError("EMAIL_RECIPIENT not configured. Set it in .env")

    subject = f"Groww Weekly Pulse — {_extract_period(pulse_text)}"
    body = pulse_text
    if doc_url:
        body += f"\n\n---\nView in Google Docs: {doc_url}"

    print(f"{'[DRY RUN] ' if dry_run else ''}Sending pulse email...")
    print(f"  To: {recipient}")
    print(f"  Subject: {subject}")

    result_raw = client.call_tool("gmail_send_email", {
        "to": [recipient],
        "subject": subject,
        "body": body,
        "body_format": "plain",
        "dry_run": dry_run,
    })

    print(f"  Result: {result_raw[:200]}")
    return result_raw


def _extract_period(pulse_text):
    match = re.search(r"\*\*Period:\*\*\s*(.+?)\s*\|", pulse_text)
    if match:
        return match.group(1).strip()
    return "This Week"


def save_fallback(pulse_text, path=None):
    path = path or FALLBACK_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pulse_text)
    print(f"  Fallback saved to {path}")


def deliver_pulse(pulse_text, recipient=None, doc_id=None, dry_run=False):
    print(f"\n{'=' * 60}")
    print("Phase 6: Delivering pulse via MCP")
    print(f"  MCP Server: {MCP_SERVER_URL}")
    print(f"  Dry run: {dry_run}")
    print(f"{'=' * 60}\n")

    client = MCPClient(MCP_SERVER_URL)
    client.initialize()
    print("MCP session initialized.\n")

    check_auth(client)
    print()

    doc_url = None
    title = f"Groww Weekly Pulse — {_extract_period(pulse_text)}"
    try:
        doc_url = publish_to_docs(
            client, pulse_text, title, doc_id=doc_id, dry_run=dry_run,
        )
        print("  Google Docs: OK\n")
    except Exception as e:
        print(f"  Google Docs FAILED: {e}")
        save_fallback(pulse_text)
        print()

    try:
        send_pulse_email(
            client, pulse_text, doc_url,
            recipient=recipient, dry_run=dry_run,
        )
        print("  Gmail: OK\n")
    except Exception as e:
        print(f"  Gmail FAILED: {e}")
        print("  Printing pulse to console as fallback:\n")
        print(pulse_text)
        print()

    print(f"{'=' * 60}")
    print("Delivery complete.")
    if doc_url:
        print(f"  Google Doc: {doc_url}")
    print(f"{'=' * 60}")

    return doc_url


if __name__ == "__main__":
    if not os.path.exists(PULSE_PATH):
        print(f"Error: {PULSE_PATH} not found. Run pulse_generator.py first.")
        exit(1)

    with open(PULSE_PATH, "r", encoding="utf-8") as f:
        pulse_text = f.read()

    print(f"Loaded pulse ({len(pulse_text.split())} words) from {PULSE_PATH}")
    deliver_pulse(pulse_text, dry_run=True)
