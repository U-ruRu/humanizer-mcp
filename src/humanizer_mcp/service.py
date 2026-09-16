from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from humanizer_mcp.models import (
    AuditResponse,
    HealthResponse,
    PrepareEditResponse,
    ValidateEditResponse,
)

VERSION = "0.1.0"
_ALLOWED_GENRES = {"marketing", "academic", "legal", "fiction", "news"}
_ALLOWED_MODES = {"edit", "audit", "targeted"}


class HumanizerService:
    def __init__(self, settings):
        self.settings = settings
        self.root = Path(settings.humanizer_root)

    def _validate_text(self, text: str, label: str = "text") -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{label} must be non-empty text")
        if len(text) > self.settings.max_text_chars:
            raise ValueError(f"{label} exceeds {self.settings.max_text_chars} characters")
        return text

    @staticmethod
    def _validate_genre(genre: str) -> str:
        if genre not in _ALLOWED_GENRES:
            raise ValueError(f"unsupported genre: {genre}")
        return genre

    def _read(self, relative: str, required: bool = True) -> str:
        path = self.root / relative
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if required:
                raise RuntimeError(f"Humanizer file is missing: {path}") from None
            return ""

    async def _scan(
        self, text: str, genre: str, before: str | None = None
    ) -> tuple[int, dict[str, Any]]:
        self._validate_text(text)
        self._validate_genre(genre)
        scanner = self.root / "scripts/scan.py"
        if not scanner.is_file():
            raise RuntimeError(f"Humanizer scanner is missing: {scanner}")

        with tempfile.TemporaryDirectory(prefix="humanizer-mcp-") as tmp:
            current = Path(tmp) / "current.txt"
            current.write_text(text, encoding="utf-8")
            args = [sys.executable, str(scanner), str(current), "--json", "--genre", genre]
            if before is not None:
                self._validate_text(before, "original")
                original = Path(tmp) / "original.txt"
                original.write_text(before, encoding="utf-8")
                args.extend(["--before", str(original)])

            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.settings.scanner_timeout_sec
                )
            except TimeoutError:
                process.kill()
                await process.communicate()
                raise RuntimeError("Humanizer scanner timed out") from None

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace").strip()
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            detail = error or output[-1000:]
            raise RuntimeError(f"Humanizer scanner returned invalid JSON: {detail}") from exc
        payload["scanner_exit_code"] = process.returncode
        return process.returncode, payload

    async def health(self) -> HealthResponse:
        skill = (self.root / "SKILL.md").is_file()
        edit_log = (self.root / "edit-log.md").is_file()
        scanner = (self.root / "scripts/scan.py").is_file()
        dependencies = {
            "razdel": importlib.util.find_spec("razdel") is not None,
            "pymorphy3": importlib.util.find_spec("pymorphy3") is not None,
        }
        scanner_smoke = False
        error = None
        if skill and edit_log and scanner and all(dependencies.values()):
            try:
                _, result = await self._scan(
                    "Это тестовый текст для проверки сервиса.", "marketing"
                )
                scanner_smoke = isinstance(result, dict) and "score" in result
            except Exception as exc:
                error = str(exc)
        else:
            missing = []
            if not skill:
                missing.append("SKILL.md")
            if not edit_log:
                missing.append("edit-log.md")
            if not scanner:
                missing.append("scripts/scan.py")
            missing.extend(name for name, present in dependencies.items() if not present)
            error = "missing: " + ", ".join(missing)

        ok = skill and edit_log and scanner and all(dependencies.values()) and scanner_smoke
        return HealthResponse(
            ok=ok,
            version=VERSION,
            humanizer_root=str(self.root),
            skill=skill,
            edit_log=edit_log,
            scanner=scanner,
            dependencies=dependencies,
            scanner_smoke=scanner_smoke,
            capabilities=["prepare_edit", "audit_text", "validate_edit"] if ok else [],
            error=error,
        )

    async def audit_text(self, text: str, genre: str = "marketing") -> AuditResponse:
        code, audit = await self._scan(text, genre)
        return AuditResponse(ok=True, genre=genre, scanner_exit_code=code, audit=audit)

    async def prepare_edit(
        self, text: str, mode: str = "edit", genre: str = "marketing"
    ) -> PrepareEditResponse:
        self._validate_text(text)
        self._validate_genre(genre)
        if mode not in _ALLOWED_MODES:
            raise ValueError(f"unsupported mode: {mode}")
        _, audit = await self._scan(text, genre)
        instructions = self._read("SKILL.md")
        edit_log = self._read("edit-log.md", required=False)
        reference_name = "references/audit.md" if mode == "audit" else "references/catalog.md"
        reference = self._read(reference_name, required=False)
        return PrepareEditResponse(
            ok=True,
            mode=mode,
            genre=genre,
            instructions=instructions,
            edit_log=edit_log,
            reference=reference,
            source_audit=audit,
        )

    async def validate_edit(
        self, original: str, edited: str, genre: str = "marketing"
    ) -> ValidateEditResponse:
        self._validate_text(original, "original")
        self._validate_text(edited, "edited")
        self._validate_genre(genre)
        code, audit = await self._scan(edited, genre, before=original)
        facts = audit.get("facts") or {}
        facts_ok = bool(facts.get("ok", code != 2))
        hard_ban_count = int(audit.get("hard_ban_count", 0) or 0)
        return ValidateEditResponse(
            ok=facts_ok and hard_ban_count == 0,
            genre=genre,
            scanner_exit_code=code,
            facts_ok=facts_ok,
            hard_ban_count=hard_ban_count,
            audit=audit,
        )
