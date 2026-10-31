from pathlib import Path

from tracekeep.migrations import migration_scripts_path

ROOT = Path(__file__).resolve().parents[2]


def test_coverage_target_cannot_be_shadowed_by_tracekeep_evidence_directory() -> None:
    configuration = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "--cov=packages/context-model/src/tracekeep" in configuration
    assert "--cov=tracekeep " not in configuration


def test_database_migrations_ship_inside_the_installable_package() -> None:
    migrations = migration_scripts_path()

    assert (migrations / "env.py").is_file()
    assert (migrations / "script.py.mako").is_file()
    assert (migrations / "versions" / "0001_context_core.py").is_file()
