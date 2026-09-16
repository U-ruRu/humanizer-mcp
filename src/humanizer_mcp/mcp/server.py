from typing import Annotated
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from humanizer_mcp.models import (
    AuditResponse,
    HealthResponse,
    PrepareEditResponse,
    ValidateEditResponse,
)

_SAFE_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _result(data, summary: str) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=summary)],
        structuredContent=data.model_dump(mode="json"),
        isError=False,
    )


def build_mcp(service, public_base_url: str):
    parsed = urlparse(public_base_url)
    hostname = parsed.hostname or "127.0.0.1"
    hosts = list(
        dict.fromkeys(
            [
                parsed.netloc,
                hostname,
                f"{hostname}:443",
                "127.0.0.1",
                "127.0.0.1:8090",
                "localhost",
                "localhost:8090",
            ]
        )
    )
    mcp = FastMCP(
        "humanizer-mcp",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=[public_base_url],
        ),
    )

    @mcp.tool(
        structured_output=True,
        annotations=_SAFE_READ_ONLY,
        description=(
            "Check whether humanizer-mcp can work end to end. Verifies the service, Humanizer RU "
            "SKILL.md, edit-log, scanner, Python dependencies, and a real scanner smoke test."
        ),
    )
    async def health() -> Annotated[CallToolResult, HealthResponse]:
        data = await service.health()
        return _result(
            data, "Humanizer MCP is healthy." if data.ok else "Humanizer MCP is unhealthy."
        )

    @mcp.tool(
        structured_output=True,
        annotations=_SAFE_READ_ONLY,
        description=(
            "Prepare Russian text for agent-side editing. Returns the authoritative Humanizer RU "
            "instructions, owner feedback log, relevant reference material, and deterministic "
            "source audit. "
            "The caller should perform the rewrite itself and then call validate_edit."
        ),
    )
    async def prepare_edit(
        text: str, mode: str = "edit", genre: str = "marketing"
    ) -> Annotated[CallToolResult, PrepareEditResponse]:
        data = await service.prepare_edit(text, mode, genre)
        return _result(data, f"Prepared Humanizer RU {mode} guidance for {genre} text.")

    @mcp.tool(
        structured_output=True,
        annotations=_SAFE_READ_ONLY,
        description=(
            "Run the deterministic Humanizer RU audit without rewriting text. Returns cleanliness "
            "score, "
            "hard bans, marker categories, rhythm, morphology, and document-structure diagnostics."
        ),
    )
    async def audit_text(
        text: str, genre: str = "marketing"
    ) -> Annotated[CallToolResult, AuditResponse]:
        data = await service.audit_text(text, genre)
        return _result(data, f"Audited {genre} text with Humanizer RU.")

    @mcp.tool(
        structured_output=True,
        annotations=_SAFE_READ_ONLY,
        description=(
            "Validate an edited Russian text against its original. Runs Humanizer RU with the "
            "fact lock, "
            "checks for added/lost facts and remaining hard bans, and reports before/after "
            "cleanliness."
        ),
    )
    async def validate_edit(
        original: str, edited: str, genre: str = "marketing"
    ) -> Annotated[CallToolResult, ValidateEditResponse]:
        data = await service.validate_edit(original, edited, genre)
        return _result(
            data, "Edited text passed validation." if data.ok else "Edited text needs another pass."
        )

    return mcp
