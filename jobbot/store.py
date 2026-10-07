"""Seen-jobs memory so you are alerted only about NEW jobs."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable


class Store:
    def __init__(self, path: Path, keep_days: int = 120):
        self.path = path
        self.keep_days = keep_days
        self.data: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:                     # noqa: BLE001
                self.data = {}

    def is_new(self, key: str) -> bool:
        return key not in self.data

    def mark(self, keys: Iterable[str]) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for k in keys:
            self.data[k] = now

    def prune(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.keep_days)
        fresh = {}
        for k, v in self.data.items():
            try:
                if datetime.fromisoformat(v) >= cutoff:
                    fresh[k] = v
            except Exception:                     # noqa: BLE001
                fresh[k] = v
        self.data = fresh

    def save(self) -> None:
        self.prune()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=0, sort_keys=True), encoding="utf-8")

    def __len__(self) -> int:
        return len(self.data)

    # ---------------- daily heartbeat helper ---------------- #
    def heartbeat_state(self) -> Dict:
        hb = self.path.parent / "heartbeat.json"
        if hb.exists():
            try:
                return json.loads(hb.read_text(encoding="utf-8"))
            except Exception:                     # noqa: BLE001
                pass
        return {}

    def set_heartbeat_state(self, state: Dict) -> None:
        hb = self.path.parent / "heartbeat.json"
        hb.parent.mkdir(parents=True, exist_ok=True)
        hb.write_text(json.dumps(state, indent=2), encoding="utf-8")
