# Third-party notices

## Humanizer RU

`humanizer-mcp` integrates with **Humanizer RU**, an independent open-source project created and maintained by **Ilya Utov / AI Frontier**.

- Upstream repository: https://github.com/ilyautov/humanizer-ru
- Author: https://github.com/ilyautov
- AI Frontier: https://aifrontier.tech/
- Live scanner demo: https://humanizer-ru.aifrontier.tech/
- Upstream license: MIT — https://github.com/ilyautov/humanizer-ru/blob/main/LICENSE

Humanizer RU provides the editing skill, rules, deterministic scanner, research references, and evaluation work. This repository provides an MCP integration layer and does not claim authorship of those upstream materials.

The Humanizer RU source is not vendored into this repository. At runtime, `humanizer-mcp` reads a separately installed Humanizer RU tree from the configured `HUMANIZER_MCP_HUMANIZER_ROOT` path (default: `/opt/humanizer-ru`). If Humanizer RU is redistributed together with this project in the future, its copyright notice and MIT license must be preserved with that distribution.
