#!/usr/bin/env python3
"""Check local Markdown links and documentation discoverability, without dependencies.

This validates the documentation structure, not application behavior or Markdown
rendering. Inline Markdown links are supported; external URLs are not fetched.
"""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "doc"
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def local_targets(path: Path, errors: list[str]) -> set[Path]:
    """Resolve inline file links relative to their Markdown source."""
    targets = set()
    content = path.read_text(encoding="utf-8")
    # Examples inside fenced blocks are not navigation links.
    content = re.sub(
        r"```[^\n]*\n.*?```",
        lambda match: "\n" * match.group(0).count("\n"),
        content,
        flags=re.S,
    )
    for match in LINK.finditer(content):
        raw = match.group(1).strip()
        if raw.startswith("<"):
            raw = raw[1:raw.find(">")]
        else:
            raw = raw.split(' "', 1)[0].split(" '", 1)[0]
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target = (path.parent / unquote(parsed.path)).resolve()
        if not target.exists():
            line = content.count("\n", 0, match.start()) + 1
            errors.append(f"{path.relative_to(ROOT)}:{line}: enlace inexistente: {raw}")
        targets.add(target)
    return targets


def main() -> int:
    errors: list[str] = []
    required = [
        ROOT / "AGENTS.md",
        ROOT / "README.md",
        DOC / "README.md",
        DOC / "contexto.md",
        DOC / "estado-actual.md",
        DOC / "continuidad.md",
        DOC / "cambios.md",
        DOC / "pendientes.md",
        DOC / "plan-implementacion.md",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Falta archivo requerido: {path.relative_to(ROOT)}")

    markdown = sorted(DOC.rglob("*.md"))
    extra = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "docs/PLAN_IMPLEMENTACION.md"]
    paths = markdown + [path for path in extra if path.is_file()]
    references = {path.resolve(): local_targets(path, errors) for path in paths}

    # Follow documentation links from its index. This catches orphan documents,
    # including ADR added without a link in their own index.
    reachable: set[Path] = set()
    pending = [(DOC / "README.md").resolve()]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(references.get(current, set()) - reachable)

    for path in markdown:
        if path.resolve() not in reachable:
            errors.append(f"Documento sin enlace desde el índice: {path.relative_to(ROOT)}")

    if errors:
        print("Documentación: FALLÓ")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Documentación: OK — {len(markdown)} Markdown en doc/, {len(paths)} archivos comprobados.")
    print("Enlaces locales e inventario accesibles. URLs externas y comportamiento de la app no comprobados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
