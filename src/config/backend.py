from deepagents.backends import (
    FilesystemBackend,
    CompositeBackend,
    StateBackend
)
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = PROJECT_ROOT / "skills"
SKILL_DIR = "/skills"

BACKEND = lambda rt: CompositeBackend(
    default=StateBackend(rt),
    routes={f"{SKILL_DIR}/": FilesystemBackend(root_dir=str(SKILLS_ROOT), virtual_mode=True)}
)


if __name__ == "__main__":
    print(PROJECT_ROOT)
    print(SKILLS_ROOT)
