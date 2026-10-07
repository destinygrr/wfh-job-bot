"""Settings + secrets loader for the WFH Job Bot."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "jobbot" / "config.yaml"


# --------------------------------------------------------------------------- #
# Minimal .env / secrets.env reader (no extra libraries needed)
# --------------------------------------------------------------------------- #
def load_env_file(path: Path) -> None:
    """Read KEY=VALUE lines into os.environ (existing env wins)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def _load_yaml_or_json(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ImportError:
        # Fallback: a config.json next to it, else built-in defaults
        alt = path.with_suffix(".json")
        if alt.exists():
            return json.loads(alt.read_text(encoding="utf-8"))
        raise SystemExit(
            "PyYAML is not installed and no config.json found.\n"
            "Run:  pip install -r requirements.txt"
        )


# --------------------------------------------------------------------------- #
@dataclass
class Profile:
    name: str
    keywords: List[str] = field(default_factory=list)
    apna_categories: List[str] = field(default_factory=list)


@dataclass
class Settings:
    profiles: List[Profile]
    location: str = "India"
    remote_only: bool = True
    sources: Dict[str, bool] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    alerts: Dict[str, Any] = field(default_factory=dict)
    state_file: str = "data/seen_jobs.json"
    digest_html: str = "data/latest_digest.html"
    digest_md: str = "data/latest_digest.md"

    # --- secrets (never stored in the config file) ---
    callmebot_phone: str = ""
    callmebot_apikey: str = ""
    telegram_token: str = ""
    telegram_chat_id: str = ""
    jooble_key: str = ""
    # ntfy.sh — free instant phone push (no account needed)
    ntfy_topic: str = ""
    ntfy_server: str = "https://ntfy.sh"

    # Green API — real WhatsApp from YOUR OWN number, free "Developer" plan
    greenapi_id: str = ""
    greenapi_token: str = ""
    greenapi_chat_id: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    mail_to: str = ""

    # ------------------------------------------------------- #
    @property
    def all_keywords(self) -> List[str]:
        out: List[str] = []
        for p in self.profiles:
            out.extend(p.keywords)
        return out

    def spread_keywords(self, limit: int) -> List[str]:
        """Round-robin across profiles so every job type gets searched equally
        (taking the first 6 keywords would only ever search profile #1)."""
        pools = [list(p.keywords) for p in self.profiles if p.keywords]
        out: List[str] = []
        idx = 0
        while len(out) < limit:
            added = False
            for pool in pools:
                if idx < len(pool) and len(out) < limit:
                    out.append(pool[idx])
                    added = True
            if not added:
                break
            idx += 1
        return out

    @property
    def all_apna_categories(self) -> List[str]:
        out: List[str] = []
        for p in self.profiles:
            out.extend(p.apna_categories)
        return out

    def keyword_to_profile(self, text: str) -> str:
        low = (text or "").lower()
        for p in self.profiles:
            if any(k.lower() in low for k in p.keywords):
                return p.name
        return self.profiles[0].name if self.profiles else "General"

    def path(self, rel: str) -> Path:
        return ROOT / rel


def load_settings(config_path: str | os.PathLike | None = None) -> Settings:
    load_env_file(ROOT / "secrets.env")
    cfg_path = Path(config_path) if config_path else DEFAULT_CONFIG
    raw = _load_yaml_or_json(cfg_path)

    profiles = [
        Profile(
            name=p.get("name", "Profile"),
            keywords=[str(k) for k in p.get("keywords", [])],
            apna_categories=[str(k) for k in p.get("apna_categories", [])],
        )
        for p in raw.get("profiles", [])
    ]
    if not profiles:
        profiles = [Profile(name="All WFH", keywords=["work from home"], apna_categories=[])]

    s = Settings(
        profiles=profiles,
        location=raw.get("location", "India"),
        remote_only=bool(raw.get("remote_only", True)),
        sources=raw.get("sources", {}) or {},
        filters=raw.get("filters", {}) or {},
        alerts=raw.get("alerts", {}) or {},
        state_file=raw.get("state_file", "data/seen_jobs.json"),
        digest_html=raw.get("digest_html", "data/latest_digest.html"),
        digest_md=raw.get("digest_md", "data/latest_digest.md"),
    )

    # secrets: environment variables (GitHub Secrets / secrets.env) win
    s.callmebot_phone = os.getenv("CALLMEBOT_PHONE", "")
    s.callmebot_apikey = os.getenv("CALLMEBOT_APIKEY", "")
    s.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    s.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    s.ntfy_topic = os.getenv("NTFY_TOPIC", "")
    s.ntfy_server = os.getenv("NTFY_SERVER", "https://ntfy.sh")
    s.greenapi_id = os.getenv("GREENAPI_ID_INSTANCE", "")
    s.greenapi_token = os.getenv("GREENAPI_API_TOKEN", "")
    s.greenapi_chat_id = os.getenv("GREENAPI_CHAT_ID", "")
    s.jooble_key = os.getenv("JOOBLE_API_KEY", "")
    s.smtp_host = os.getenv("SMTP_HOST", "")
    s.smtp_port = int(os.getenv("SMTP_PORT", "587") or 587)
    s.smtp_user = os.getenv("SMTP_USER", "")
    s.smtp_pass = os.getenv("SMTP_PASS", "")
    s.mail_to = os.getenv("MAIL_TO", "")
    if s.mail_to == "" and os.getenv("SMTP_USER"):
        s.mail_to = os.getenv("SMTP_USER", "")
    return s
