# ruff: noqa: E501
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

PRIVACY = """<!doctype html><html><meta charset="utf-8"><title>Privacy Policy</title><body><h1>Privacy Policy</h1><p>humanizer-mcp processes text submitted by authorized clients to provide Humanizer RU editing guidance, deterministic audits, and edit validation. OAuth state and technical service data may be stored on the service owner's server. Submitted text is processed for the requested operation and is not sold.</p><p>Effective date: 2026-09-16.</p></body></html>"""


def build_public_router():
    router = APIRouter()

    @router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
    async def privacy():
        return HTMLResponse(PRIVACY)

    return router
