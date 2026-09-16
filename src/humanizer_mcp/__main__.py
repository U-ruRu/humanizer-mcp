import uvicorn

from humanizer_mcp.config import Settings


def main():
    settings = Settings()
    uvicorn.run("humanizer_mcp.app:app", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
