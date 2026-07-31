from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"YAML okunamadı: {path}: {exc}") from exc


def validate_components(errors: list[str]) -> None:
    path = PROJECT_ROOT / "config/architecture/components.yaml"
    document = load_yaml(path)
    components = document.get("components", [])
    ids = [item.get("module_id") for item in components]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"Tekrarlanan module_id: {', '.join(duplicates)}")

    known = set(ids)
    for component in components:
        module_id = component.get("module_id")
        for producer in component.get("input_producers", []):
            if producer not in known and producer != "external":
                errors.append(f"{module_id}: bilinmeyen input producer '{producer}'.")
        for consumer in component.get("output_consumers", []):
            if consumer not in known and consumer != "external":
                errors.append(f"{module_id}: bilinmeyen output consumer '{consumer}'.")


def validate_algorithms(errors: list[str]) -> None:
    path = PROJECT_ROOT / "config/algorithms/algorithm_registry.yaml"
    document = load_yaml(path)
    algorithms = document.get("algorithms", [])
    source_document = load_yaml(PROJECT_ROOT / "config/sources/sources.yaml")
    known_references = {item.get("reference_id") for item in source_document.get("sources", [])}
    ids = [item.get("algorithm_id") for item in algorithms]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"Tekrarlanan algorithm_id: {', '.join(duplicates)}")
    for algorithm in algorithms:
        for field in ("algorithm_id", "name", "module_id", "status", "odd_profiles", "references"):
            if not algorithm.get(field):
                errors.append(f"Algoritma alanı eksik: {algorithm.get('algorithm_id', '<unknown>')}.{field}")
        for reference_id in algorithm.get("references", []):
            if reference_id not in known_references:
                errors.append(
                    f"{algorithm.get('algorithm_id')}: bilinmeyen kaynak '{reference_id}'."
                )


def validate_module_docs(errors: list[str]) -> None:
    python_modules = sorted(
        path.parent for path in PROJECT_ROOT.glob("autonomy/**/__init__.py") if path.parent != PROJECT_ROOT / "autonomy"
    )
    for module_dir in python_modules:
        module_doc = module_dir / "MODULE.md"
        if not module_doc.is_file():
            errors.append(f"MODULE.md eksik: {module_dir.relative_to(PROJECT_ROOT)}")


def main() -> int:
    errors: list[str] = []
    validate_components(errors)
    validate_algorithms(errors)
    validate_module_docs(errors)
    if errors:
        print("[HATA] Proje doğrulaması başarısız:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("[OK] Registry, modül dokümanları ve temel proje sözleşmeleri tutarlı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
