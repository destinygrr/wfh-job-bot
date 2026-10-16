"""Gmail → WhatsApp: alerts you about JOB-RELATED emails in your Gmail inbox.

Why this is safe and simple:
  * Uses IMAP + a Gmail **App Password** (no OAuth, no Google Cloud project,
    nothing that expires weekly).
  * Opens the inbox **read-only** — your emails are never marked as read,
    moved or deleted.
  * Every email is reported only once (deduped by Message-ID).

Setup (one time, 5 minutes):
  1. Google Account -> Security -> turn ON "2-Step Verification"
  2. Open https://myaccount.google.com/apppasswords -> create an app password
     (name it "wfh-bot") -> you get a 16-character password
  3. Add two secrets:
        GMAIL_USER          = yourname@gmail.com
        GMAIL_APP_PASSWORD  = the 16-character app password (spaces are fine)
  4. In config.yaml -> gmail: enabled: true
"""
from __future__ import annotations

import email
import hashlib
import imaplib
import json
import re
from datetime import datetime, timedelta, timezone
from email.header import decode_header, make_header
from pathlib import Path
from typing import Dict, List, Tuple

IMAP_HOST = "imap.gmail.com"

DEFAULT_SENDERS = [
    "linkedin.com", "naukri.com", "apna.co", "indeed.com", "foundit.in",
    "hirist.com", "instahyre.com", "glassdoor.com", "iimjobs.com",
    "naukrigulf.com", "timesjobs.com", "monsterindia.com", "cutshort.io",
    "wellfound.com", "angel.co", "freshersworld.com",
]
DEFAULT_KEYWORDS = [
    "job", "application", "interview", "opportunity", "recruiter", "hiring",
    "shortlist", "profile", "vacancy", "opening", "candidate",
]
DEFAULT_EXCLUDE = ["newsletter", "webinar", "promotion", "sponsored", "course"]


# --------------------------------------------------------------------------- #
def _dec(value) -> str:
    """Decode MIME-encoded headers (e.g. =?UTF-8?B?...?=) into plain text."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:                             # noqa: BLE001
        return str(value).strip()


def _body_snippet(msg, limit: int = 220) -> str:
    """First bit of readable text from the email (for interview invites etc.)."""
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    text = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", "ignore")
                except Exception:                 # noqa: BLE001
                    text = ""
                if text.strip():
                    break
    else:
        try:
            text = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", "ignore")
        except Exception:                         # noqa: BLE001
            text = ""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(https?://\S+)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _is_job_email(sender: str, subject: str, gcfg: Dict) -> bool:
    s_low, subj_low = sender.lower(), subject.lower()
    senders = [s.lower() for s in (gcfg.get("job_senders") or DEFAULT_SENDERS)]
    keywords = [k.lower() for k in (gcfg.get("subject_keywords") or DEFAULT_KEYWORDS)]
    excludes = [e.lower() for e in (gcfg.get("exclude_subjects") or DEFAULT_EXCLUDE)]

    if any(e in subj_low for e in excludes):
        return False
    from_known = any(dom in s_low for dom in senders)
    kw_hit = any(re.search(rf"\b{re.escape(k)}", subj_low) for k in keywords)
    return from_known or kw_hit


# --------------------------------------------------------------------------- #
class EmailStore:
    """Remembers which emails were already alerted (never alerts twice)."""

    def __init__(self, path: Path, keep_days: int = 120):
        self.path = path
        self.keep_days = keep_days
        self.data: Dict[str, str] = {}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:                     # noqa: BLE001
                self.data = {}

    def seen(self, mid: str) -> bool:
        return mid in self.data

    def mark(self, mids: List[str]) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for m in mids:
            self.data[m] = now

    def save(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.keep_days)
        fresh = {}
        for k, v in self.data.items():
            try:
                if datetime.fromisoformat(v) >= cutoff:
                    fresh[k] = v
            except Exception:                     # noqa: BLE001
                fresh[k] = v
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(fresh, indent=0, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------- #
def fetch_job_emails(s) -> Tuple[List[Dict], str]:
    """Read the inbox (read-only) and return NEW job-related emails."""
    gcfg = s.gmail or {}
    if not gcfg.get("enabled", False):
        return [], "skipped (gmail: enabled is false in config.yaml)"
    if not (s.gmail_user and s.gmail_app_password):
        return [], "skipped (GMAIL_USER / GMAIL_APP_PASSWORD not set)"
    try:
        days = int(gcfg.get("lookback_days", 3))
        since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%d-%b-%Y")
        store = EmailStore(s.path("data/seen_emails.json"))

        box = imaplib.IMAP4_SSL(IMAP_HOST, 993)
        box.login(s.gmail_user, s.gmail_app_password.replace(" ", ""))
        box.select("INBOX", readonly=True)        # read-only: we never alter the inbox

        typ, data = box.search(None, f'(SINCE "{since}")')
        uids = (data[0].split() if data and data[0] else [])[-int(gcfg.get("max_scan", 80)):]
        found: List[Dict] = []
        for uid in reversed(uids):                # newest first
            typ, msg_data = box.fetch(uid, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            mid = _dec(msg.get("Message-ID")) or hashlib.sha1(msg_data[0][1][:500]).hexdigest()
            sender = _dec(msg.get("From"))
            subject = _dec(msg.get("Subject"))
            if not _is_job_email(sender, subject, gcfg):
                continue
            if store.seen(mid):
                continue
            found.append({
                "mid": mid,
                "from": sender,
                "subject": subject,
                "date": _dec(msg.get("Date")),
                "snippet": _body_snippet(msg),
            })
            if len(found) >= int(gcfg.get("max_per_alert", 8)):
                break
        box.logout()

        if found:
            store.mark([f["mid"] for f in found])
            store.save()
        return found, f"{len(found)} new job email(s)"
    except imaplib.IMAP4.error as exc:
        return [], f"gmail login failed: {str(exc)[:110]} (check the app password)"
    except Exception as exc:                      # noqa: BLE001
        return [], f"error: {type(exc).__name__}"


def _short_date(raw: str) -> str:
    try:
        dt = email.utils.parsedate_to_datetime(raw)
        ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
        return ist.strftime("%d %b, %I:%M %p")
    except Exception:                             # noqa: BLE001
        return (raw or "")[:16]


def format_email_alert(emails: List[Dict]) -> str:
    lines = [f"📧 JOB EMAILS — {len(emails)} new", ""]
    for i, e in enumerate(emails, 1):
        who = e["from"].split("<")[0].strip().strip('"')[:34] or "Unknown sender"
        lines.append(f"{i}) {who} — {e['subject'][:80] or '(no subject)'}")
        lines.append(f"   {_short_date(e['date'])}" + (f" · {e['snippet'][:90]}" if e["snippet"] else ""))
        lines.append("")
    lines.append("Open Gmail on your phone to reply or check the details.")
    return "\n".join(lines)
