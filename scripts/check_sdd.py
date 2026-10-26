#!/usr/bin/env python3
"""Validate local SDD references and evidence declarations, not app behavior."""

import argparse
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT = r"(?:PRD|TRD)-\d{2}"
TASK = r"(?:P\d+B?|M\d+)-\d{2}"
TEST = r"T-\d{2}"
STATES = {"borrador", "en-revision", "lista", "implementada", "verificada", "sustituida"}
FIELDS = {"ID", "Estado", "Requisitos", "Tareas", "Pruebas", "Cambio", "Evidencia"}


def validate(root: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    """Return structural errors and parsed specs from an isolated repository root."""
    root = root.resolve()
    doc = root / "doc"
    errors: list[str] = []

    def read(path: Path) -> str:
        if not path.is_file():
            errors.append(f"Falta archivo: {path.relative_to(root)}")
            return ""
        return path.read_text(encoding="utf-8")

    requirements = []
    for name in ("PRD.md", "TRD.md"):
        requirements.extend(re.findall(rf"^### ({REQUIREMENT})\b", read(doc / name), re.M))
    if len(requirements) != len(set(requirements)):
        errors.append("Hay IDs PRD/TRD duplicados en sus definiciones")
    known_requirements = set(requirements)
    if not known_requirements:
        errors.append("No hay requisitos PRD/TRD definidos")
    tasks = set(re.findall(rf"^\|\s*({TASK})\s*\|", read(doc / "plan-implementacion.md"), re.M))
    tests = set(re.findall(rf"^\|\s*({TEST})\s*\|", read(doc / "pruebas.md"), re.M))
    changes = set(re.findall(r"^## (CAM-\d{3})\b", read(doc / "cambios.md"), re.M))

    matrix: dict[str, set[str]] = {}
    for line in read(doc / "trazabilidad.md").splitlines():
        if not line.startswith("|"):
            continue
        spec_id = re.search(r"\[(SPEC-\d{3})\]", line)
        if spec_id:
            key = spec_id.group(1)
            if key in matrix:
                errors.append(f"{key}: fila duplicada en trazabilidad")
            matrix[key] = set(re.findall(REQUIREMENT, line))

    specs: dict[str, dict[str, str]] = {}
    covered: set[str] = set()
    criteria_seen: set[str] = set()
    paths = sorted((doc / "especificaciones").glob("SPEC-*.md"))
    if not paths:
        errors.append("No hay especificaciones SPEC-*.md")
    for path in paths:
        content = read(path)
        metadata: dict[str, str] = {}
        for key, value in re.findall(r"^(\w+):[ \t]*(.*)$", content, re.M):
            if key in FIELDS:
                if key in metadata:
                    errors.append(f"{path.name}: metadato duplicado {key}")
                metadata[key] = value.strip()
        for field in FIELDS - metadata.keys():
            errors.append(f"{path.name}: falta metadato {field}")
        spec_id = metadata.get("ID", "")
        if not re.fullmatch(r"SPEC-\d{3}", spec_id) or not path.name.startswith(spec_id + "-"):
            errors.append(f"{path.name}: ID incompatible con el nombre de archivo")
            continue
        if spec_id in specs:
            errors.append(f"{spec_id}: ID de especificación duplicado")
        specs[spec_id] = metadata
        if metadata.get("Estado") not in STATES:
            errors.append(f"{spec_id}: estado desconocido")

        def refs(field: str, pattern: str, known: set[str]) -> set[str]:
            values = [item.strip() for item in metadata.get(field, "").split(",") if item.strip()]
            if not values:
                errors.append(f"{spec_id}: {field} vacío")
            if len(values) != len(set(values)):
                errors.append(f"{spec_id}: {field} contiene duplicados")
            for value in values:
                if not re.fullmatch(pattern, value) or value not in known:
                    errors.append(f"{spec_id}: referencia desconocida en {field}: {value}")
            return set(values)

        reqs = refs("Requisitos", REQUIREMENT, known_requirements)
        refs("Tareas", TASK, tasks)
        declared_tests = refs("Pruebas", TEST, tests)
        covered.update(reqs)
        if matrix.get(spec_id) != reqs:
            errors.append(f"{spec_id}: matriz de trazabilidad ausente o distinta de sus requisitos")

        count = 0
        for line in content.splitlines():
            if not re.match(r"^\|\s*CA-", line):
                continue
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            criterion = cells[0] if cells else ""
            if len(cells) != 3 or not re.fullmatch(rf"CA-{spec_id[-3:]}-\d{{2}}", criterion):
                errors.append(f"{spec_id}: criterio mal formado: {criterion}")
                continue
            count += 1
            if criterion in criteria_seen:
                errors.append(f"{spec_id}: criterio duplicado: {criterion}")
            criteria_seen.add(criterion)
            criterion_tests = set(re.findall(TEST, cells[2]))
            if not cells[1] or not criterion_tests or not criterion_tests <= declared_tests:
                errors.append(f"{spec_id}: {criterion} sin descripción/pruebas declaradas válidas")
        if not count:
            errors.append(f"{spec_id}: no tiene criterios de aceptación")

        change = metadata.get("Cambio", "")
        if change != "pendiente" and change not in changes:
            errors.append(f"{spec_id}: CAM desconocido: {change}")
        if metadata.get("Estado") == "verificada":
            evidence = metadata.get("Evidencia", "")
            target = (path.parent / evidence).resolve()
            if change not in changes or evidence == "pendiente" or not evidence:
                errors.append(f"{spec_id}: verificada exige CAM y evidencia")
            elif not target.is_relative_to(root) or not target.is_file():
                errors.append(f"{spec_id}: evidencia inexistente o fuera del repositorio")

    for requirement in sorted(known_requirements - covered):
        errors.append(f"Requisito sin especificación: {requirement}")
    for spec_id in sorted(matrix.keys() - specs.keys()):
        errors.append(f"Matriz referencia SPEC inexistente: {spec_id}")
    return errors, specs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", help="Limitar resumen a una SPEC, sin omitir integridad global")
    args = parser.parse_args()
    errors, specs = validate(ROOT)
    if args.spec and args.spec not in specs:
        errors.append(f"Especificación desconocida: {args.spec}")
    if errors:
        print("SDD: FALLÓ")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"SDD: OK — {len(specs)} especificaciones con trazabilidad estructural válida.")
    for spec_id, metadata in specs.items():
        if not args.spec or args.spec == spec_id:
            print(f"- {spec_id}: {metadata['Estado']}")
    print("No verifica comportamiento, rendimiento ni veracidad semántica de la evidencia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
