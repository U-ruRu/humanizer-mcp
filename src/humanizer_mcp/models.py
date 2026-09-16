from typing import Any, Literal

from pydantic import BaseModel

Genre = Literal["marketing", "academic", "legal", "fiction", "news"]
EditMode = Literal["edit", "audit", "targeted"]


class HealthResponse(BaseModel):
    ok: bool
    application: str = "humanizer-mcp"
    version: str
    humanizer_root: str
    skill: bool
    edit_log: bool
    scanner: bool
    dependencies: dict[str, bool]
    scanner_smoke: bool
    capabilities: list[str]
    error: str | None = None


class AuditResponse(BaseModel):
    ok: bool
    genre: str
    scanner_exit_code: int
    audit: dict[str, Any]


class PrepareEditResponse(BaseModel):
    ok: bool
    mode: str
    genre: str
    instructions: str
    edit_log: str
    reference: str
    source_audit: dict[str, Any]


class ValidateEditResponse(BaseModel):
    ok: bool
    genre: str
    scanner_exit_code: int
    facts_ok: bool
    hard_ban_count: int
    audit: dict[str, Any]
