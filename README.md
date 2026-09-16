# humanizer-mcp

`humanizer-mcp` exposes the existing Humanizer RU skill as a narrow MCP service. The server performs deterministic analysis and returns the authoritative editing instructions to the calling language model. The language model remains responsible for the actual rewrite.

## MCP tools

- `health` — end-to-end readiness: service, `SKILL.md`, `edit-log.md`, scanner, Python dependencies, scanner smoke test.
- `prepare_edit` — Humanizer instructions + owner feedback + reference material + source audit.
- `audit_text` — deterministic Humanizer RU audit without rewriting.
- `validate_edit` — fact-lock and final scan against the original text.

The service deliberately exposes no shell execution.

## Runtime

Default Humanizer location: `/opt/humanizer-ru`.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
cp .env.example .env
.venv/bin/humanizer-mcp
```

MCP endpoint: `/mcp` using Streamable HTTP. OAuth metadata and dynamic client registration follow the same PKCE-based pattern used by `terminal-mcp`.

## Editing flow

1. Call `health`.
2. Call `prepare_edit` with the source text, mode and genre.
3. Apply the returned `SKILL.md` rules in the caller model.
4. Call `validate_edit` with the original and edited text.
5. Repeat the local edit when the fact lock fails or hard bans remain.

## Genres

`marketing`, `academic`, `legal`, `fiction`, `news`.

## Security

Text size is capped by `HUMANIZER_MCP_MAX_TEXT_CHARS`. The MCP has no terminal surface and can read only the configured Humanizer files through the domain service. OAuth state is stored in SQLite.

## Runtime permissions

`/opt/humanizer-ru` can remain owned by `root`. Deployment creates the `humanizer-readers` group, adds the `humanizer-mcp` service account to it, grants group read/execute access to the Humanizer tree, and sets the setgid bit on its directories so newly created files inherit the reader group. The systemd service mounts the Humanizer and release trees read-only and gives the process write access only to `/var/lib/humanizer-mcp`.

The default production service uses OAuth. A loopback-only smoke deployment may temporarily set `HUMANIZER_MCP_AUTH_MODE=none`; public exposure requires OAuth or another configured authentication mode.
