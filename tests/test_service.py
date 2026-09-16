from pathlib import Path

import pytest

from humanizer_mcp.config import Settings
from humanizer_mcp.service import HumanizerService

SCANNER = r"""import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("source")
parser.add_argument("--json", action="store_true")
parser.add_argument("--genre")
parser.add_argument("--before")
args = parser.parse_args()
text = open(args.source, encoding="utf-8").read()
facts = {"ok": True}
if args.before:
    original = open(args.before, encoding="utf-8").read()
    facts = {"ok": "999" not in text or "999" in original}
out = {
    "score": {"score": 91},
    "hard_ban_count": 1 if "BAN" in text else 0,
    "facts": facts,
    "genre": args.genre,
}
print(json.dumps(out, ensure_ascii=False))
raise SystemExit(2 if not facts["ok"] else (1 if out["hard_ban_count"] else 0))
"""


def make_humanizer(root: Path):
    (root / "scripts").mkdir(parents=True)
    (root / "references").mkdir()
    (root / "SKILL.md").write_text("# Humanizer test skill\nKeep facts.", encoding="utf-8")
    (root / "edit-log.md").write_text("# feedback\n", encoding="utf-8")
    (root / "references/catalog.md").write_text("# catalog\n", encoding="utf-8")
    (root / "references/audit.md").write_text("# audit\n", encoding="utf-8")
    (root / "scripts/scan.py").write_text(SCANNER, encoding="utf-8")


@pytest.fixture
def service(tmp_path):
    root = tmp_path / "humanizer"
    make_humanizer(root)
    settings = Settings(
        humanizer_root=root,
        database_path=tmp_path / "oauth.sqlite3",
        auth_mode="none",
    )
    return HumanizerService(settings)


@pytest.mark.asyncio
async def test_health_reports_end_to_end_readiness(service):
    health = await service.health()
    assert health.ok is True
    assert health.skill is True
    assert health.scanner_smoke is True
    assert health.capabilities == ["prepare_edit", "audit_text", "validate_edit"]


@pytest.mark.asyncio
async def test_prepare_edit_returns_skill_feedback_reference_and_audit(service):
    result = await service.prepare_edit("Нормальный исходный текст.", "edit", "marketing")
    assert result.ok is True
    assert "Humanizer test skill" in result.instructions
    assert "feedback" in result.edit_log
    assert "catalog" in result.reference
    assert result.source_audit["score"]["score"] == 91


@pytest.mark.asyncio
async def test_audit_accepts_hard_ban_exit_code(service):
    result = await service.audit_text("Текст с BAN.")
    assert result.ok is True
    assert result.scanner_exit_code == 1
    assert result.audit["hard_ban_count"] == 1


@pytest.mark.asyncio
async def test_validate_edit_checks_fact_lock_and_hard_bans(service):
    good = await service.validate_edit("Цена 100 рублей.", "Цена 100 рублей.")
    assert good.ok is True
    assert good.facts_ok is True

    added_fact = await service.validate_edit("Цена 100 рублей.", "Цена 999 рублей.")
    assert added_fact.ok is False
    assert added_fact.facts_ok is False
    assert added_fact.scanner_exit_code == 2

    banned = await service.validate_edit("Исходник.", "BAN Исходник.")
    assert banned.ok is False
    assert banned.facts_ok is True
    assert banned.hard_ban_count == 1
