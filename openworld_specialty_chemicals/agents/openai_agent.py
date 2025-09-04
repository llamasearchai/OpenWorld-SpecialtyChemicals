from __future__ import annotations

import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

from .base import AdviceAgent
import logging

try:
    import sqlite_utils  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sqlite_utils = None  # type: ignore


SYSTEM_PROMPT = (
    "You advise on specialty-chemicals effluent treatment. "
    "Given alerts (species, value, limit), propose concise actions and a short rationale. "
    "Only output JSON with keys 'actions' (list of strings) and 'rationale' (string)."
)


class OpenAIAdviceAgent(AdviceAgent):
    def __init__(
        self,
        model: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        breaker_threshold: int = 5,
        breaker_window_sec: float = 60.0,
        cache_path: Optional[Path] = None,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        key = os.getenv("OPENAI_API_KEY")
        if OpenAI is None or not key:
            raise RuntimeError("OpenAI client not available; install extras 'ai' and set OPENAI_API_KEY")
        self.client = OpenAI(api_key=key)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.breaker_threshold = breaker_threshold
        self.breaker_window_sec = breaker_window_sec
        self._failures: List[float] = []
        self.log = logging.getLogger("agents.openai")

        # Persistent cache (optional)
        default_cache = Path.home() / ".cache" / "openworld_specialty_chemicals" / "agent_cache.sqlite"
        self.cache_path = cache_path or default_cache
        self.cache_db = None
        if sqlite_utils is not None:
            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                self.cache_db = sqlite_utils.Database(self.cache_path)
                if "cache" not in self.cache_db.table_names():
                    self.cache_db["cache"].create({"key": str, "value": str, "ts": float}, pk="key")
            except Exception:
                self.cache_db = None  # pragma: no cover

    def _sanitize_alerts(self, alerts: Iterable[Dict]) -> List[Dict[str, object]]:
        arr: List[Dict[str, object]] = []
        for a in alerts:
            if not isinstance(a, dict):
                continue
            species = str(a.get("species", ""))[:64]
            try:
                value = float(a.get("value", 0.0))
                limit = float(a.get("limit", 0.0))
                t = float(a.get("time", 0.0))
            except Exception:
                continue
            arr.append({"time": t, "species": species, "value": value, "limit": limit})
            if len(arr) >= 128:
                break
        return arr

    def _cache_key(self, model: str, payload: List[Dict[str, object]]) -> str:
        h = hashlib.sha256()
        h.update(model.encode("utf-8"))
        h.update(json.dumps(payload, sort_keys=True).encode("utf-8"))
        return h.hexdigest()

    def _cache_get(self, key: str) -> Optional[Dict[str, object]]:
        if not self.cache_db:
            return None
        try:
            row = self.cache_db["cache"].get(key)  # type: ignore[attr-defined]
            if row:
                return json.loads(row["value"])  # type: ignore[index]
        except Exception:
            return None
        return None

    def _cache_set(self, key: str, value: Dict[str, object]) -> None:
        if not self.cache_db:
            return
        try:
            self.cache_db["cache"].upsert({"key": key, "value": json.dumps(value, ensure_ascii=False), "ts": time.time()})  # type: ignore[attr-defined]
        except Exception:
            pass

    def _breaker_open(self) -> bool:
        now = time.time()
        self._failures = [t for t in self._failures if now - t <= self.breaker_window_sec]
        return len(self._failures) >= self.breaker_threshold

    def _record_failure(self) -> None:
        self._failures.append(time.time())

    def advise(self, alerts: Iterable[Dict]) -> Dict[str, object]:
        payload = self._sanitize_alerts(alerts)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"alerts": payload}, ensure_ascii=False)},
        ]

        key = self._cache_key(self.model, payload)
        cached = self._cache_get(key)
        if cached is not None:
            self.log.debug("cache_hit: model=%s payload_size=%d", self.model, len(payload))
            return cached

        if self._breaker_open():
            self.log.warning("circuit_open: skipping call to provider")
            return {"actions": ["Check process"], "rationale": "Upstream unavailable (circuit open)."}

        attempt = 0
        start_all = time.time()
        while True:
            attempt += 1
            t0 = time.time()
            try:
                self.log.debug("agent_call: attempt=%d model=%s", attempt, self.model)
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0, timeout=self.timeout
                )
                text = resp.choices[0].message.content or "{}"
                out = json.loads(text)
                if not isinstance(out.get("actions"), list):
                    out["actions"] = ["Check process"]
                if not isinstance(out.get("rationale"), str):
                    out["rationale"] = "Model returned invalid rationale."
                self.log.info(
                    "agent_ok: ms=%d model=%s tokens=?", int((time.time() - t0) * 1000), self.model
                )
                self._cache_set(key, out)
                return out
            except Exception as exc:  # pragma: no cover - depends on network failures
                self._record_failure()
                self.log.warning(
                    "agent_error: attempt=%d err=%s", attempt, getattr(exc, "__class__", type(exc)).__name__
                )
                if attempt >= self.max_retries:
                    break
                backoff = self.backoff_base * (2 ** (attempt - 1))
                time.sleep(backoff)
        self.log.error(
            "agent_failed: total_ms=%d attempts=%d", int((time.time() - start_all) * 1000), attempt
        )
        return {"actions": ["Check process"], "rationale": "Failed to retrieve advice."}

