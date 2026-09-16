import contextlib

from fastapi import FastAPI
from starlette.routing import Mount

from humanizer_mcp.auth.credentials import CredentialManager
from humanizer_mcp.auth.middleware import AuthMiddleware
from humanizer_mcp.auth.routes import build_oauth_router
from humanizer_mcp.auth.service import AuthService
from humanizer_mcp.auth.storage import OAuthStore
from humanizer_mcp.config import Settings
from humanizer_mcp.http.public import build_public_router
from humanizer_mcp.http.rate_limit import RateLimitMiddleware
from humanizer_mcp.mcp.server import build_mcp
from humanizer_mcp.service import VERSION, HumanizerService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    service = HumanizerService(settings)
    oauth_store = OAuthStore(settings.database_path)
    credentials = CredentialManager(settings)
    auth = AuthService(settings, oauth_store, credentials)
    mcp = build_mcp(service, settings.public_base_url)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        await oauth_store.initialize()
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="humanizer-mcp", version=VERSION, lifespan=lifespan)
    app.state.settings = settings
    app.state.service = service
    app.include_router(build_public_router())
    app.include_router(build_oauth_router(settings, auth, oauth_store))
    app.router.routes.append(Mount("/mcp", app=mcp.streamable_http_app()))

    @app.get("/health/live", include_in_schema=False)
    async def live():
        return {"ok": True, "application": "humanizer-mcp", "version": VERSION}

    app.add_middleware(AuthMiddleware, settings=settings, auth_service=auth)
    app.add_middleware(RateLimitMiddleware)
    return app


app = create_app()
