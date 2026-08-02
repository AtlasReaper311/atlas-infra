#!/usr/bin/env python3
"""Validate the normative AtlasField composition catalogue."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATALOGUE_SCHEMA = "atlas-control-plane/atlasfield-composition-catalogue/v1"
EXPECTED_COMPOSITIONS = (
    "identity-field",
    "proof-trace",
    "pulse-horizon",
    "signal-bloom",
    "telemetry-lattice",
)
EXPECTED_ROUTES = (
    "/about/",
    "/systems/evidence/",
    "/systems/reliability/",
    "/lab/",
    "/systems/observability/",
)
ALLOWED_PRESETS = ("hero", "ambient", "card")
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "status",
    "catalogue_fingerprint",
    "authority",
    "scope",
    "renderer",
    "composition_defaults",
    "compositions",
    "validation_requirements",
}
REQUIRED_COMPOSITION_KEYS = {
    "name",
    "route",
    "surface",
    "selector",
    "preset",
    "state_key",
    "host_classes",
    "canvas_class",
    "seed",
    "density",
    "domain_breaks",
    "domain_styles",
    "light",
    "visual_contract",
    "evidence_contract",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    fingerprint: str | None = None

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return document


def canonical_bytes(document: dict[str, Any]) -> bytes:
    candidate = copy.deepcopy(document)
    candidate["catalogue_fingerprint"] = None
    return json.dumps(
        candidate,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def catalogue_fingerprint(document: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_catalogue(document: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    require(
        set(document) == REQUIRED_TOP_LEVEL_KEYS,
        "catalogue top-level keys are missing or unexpected",
        errors,
    )
    require(
        document.get("schema_version") == CATALOGUE_SCHEMA,
        "catalogue schema_version is invalid",
        errors,
    )
    require(document.get("status") == "accepted", "catalogue status is not accepted", errors)

    fingerprint = catalogue_fingerprint(document)
    require(
        document.get("catalogue_fingerprint") == fingerprint,
        "catalogue_fingerprint does not match canonical content",
        errors,
    )

    authority = document.get("authority", {})
    require(isinstance(authority, dict), "authority must be an object", errors)
    if isinstance(authority, dict):
        require(
            authority.get("programme_phase") == "Phase 13",
            "programme phase is invalid",
            errors,
        )
        require(
            authority.get("source_repository") == "AtlasReaper311/atlas-systems",
            "source repository is invalid",
            errors,
        )
        require(
            isinstance(authority.get("source_main_sha"), str)
            and re.fullmatch(r"[0-9a-f]{40}", authority["source_main_sha"]) is not None,
            "source_main_sha must be a full git SHA",
            errors,
        )
        for key in (
            "programme_record",
            "catalogue_document",
            "source_contract",
            "source_registry",
            "validator",
        ):
            require(
                isinstance(authority.get(key), str) and bool(authority[key]),
                f"authority.{key} is required",
                errors,
            )

    scope = document.get("scope", {})
    require(isinstance(scope, dict), "scope must be an object", errors)
    if isinstance(scope, dict):
        require(
            scope.get("kind") == "documentation-and-validation",
            "scope kind is invalid",
            errors,
        )
        for key in (
            "public_route_created",
            "renderer_source_changed",
            "product_runtime_changed",
            "provider_or_secret_changed",
        ):
            require(scope.get(key) is False, f"scope.{key} must be false", errors)

    renderer = document.get("renderer", {})
    require(isinstance(renderer, dict), "renderer must be an object", errors)
    if isinstance(renderer, dict):
        require(
            tuple(renderer.get("allowed_presets", [])) == ALLOWED_PRESETS,
            "allowed presets are invalid",
            errors,
        )
        modules = renderer.get("public_modules", [])
        require(
            isinstance(modules, list) and len(modules) == 3,
            "renderer public modules are invalid",
            errors,
        )
        for module in modules if isinstance(modules, list) else []:
            require(
                isinstance(module, str) and module.startswith("/static/"),
                "renderer module paths must be static absolute paths",
                errors,
            )

    defaults = document.get("composition_defaults", {})
    require(isinstance(defaults, dict), "composition_defaults must be an object", errors)
    if isinstance(defaults, dict):
        require(
            defaults.get("preset") == "ambient",
            "default preset must be ambient",
            errors,
        )
        require(
            defaults.get("pointer_enabled") is False,
            "default pointer must be disabled",
            errors,
        )
        require(
            defaults.get("state_key") == "atlasCompositionState",
            "default state key is invalid",
            errors,
        )
        require(
            defaults.get("canvas_class") == "atlas-composition-canvas",
            "default canvas class is invalid",
            errors,
        )

    compositions = document.get("compositions", [])
    require(
        isinstance(compositions, list) and bool(compositions),
        "compositions must be a non-empty list",
        errors,
    )
    if isinstance(compositions, list):
        names = [item.get("name") for item in compositions if isinstance(item, dict)]
        routes = [item.get("route") for item in compositions if isinstance(item, dict)]
        require(
            tuple(names) == EXPECTED_COMPOSITIONS,
            "composition names are invalid or out of order",
            errors,
        )
        require(
            tuple(routes) == EXPECTED_ROUTES,
            "composition routes are invalid or out of order",
            errors,
        )
        require(len(names) == len(set(names)), "composition names must be unique", errors)
        require(len(routes) == len(set(routes)), "composition routes must be unique", errors)
        for index, composition in enumerate(compositions):
            require(isinstance(composition, dict), f"compositions[{index}] must be an object", errors)
            if not isinstance(composition, dict):
                continue
            require(
                set(composition) == REQUIRED_COMPOSITION_KEYS,
                f"compositions[{index}] keys are missing or unexpected",
                errors,
            )
            name = composition.get("name")
            route = composition.get("route")
            selector = composition.get("selector")
            require(
                isinstance(name, str)
                and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None,
                f"compositions[{index}].name is invalid",
                errors,
            )
            require(
                isinstance(route, str)
                and route.startswith("/")
                and route.endswith("/"),
                f"compositions[{index}].route must be canonical",
                errors,
            )
            require(
                isinstance(selector, str) and selector.startswith("."),
                f"compositions[{index}].selector must be a class selector",
                errors,
            )
            require(
                composition.get("preset") == "ambient",
                f"compositions[{index}].preset must be ambient",
                errors,
            )
            require(
                isinstance(composition.get("surface"), str)
                and bool(composition["surface"]),
                f"compositions[{index}].surface is required",
                errors,
            )
            require(
                isinstance(composition.get("state_key"), str)
                and bool(composition["state_key"]),
                f"compositions[{index}].state_key is required",
                errors,
            )
            require(
                composition.get("canvas_class") == "atlas-composition-canvas",
                f"compositions[{index}].canvas_class is invalid",
                errors,
            )
            require(
                isinstance(composition.get("seed"), str)
                and composition["seed"].startswith("atlas-"),
                f"compositions[{index}].seed is invalid",
                errors,
            )
            host_classes = composition.get("host_classes", [])
            require(
                isinstance(host_classes, list) and len(host_classes) == 2,
                f"compositions[{index}].host_classes is invalid",
                errors,
            )
            if isinstance(host_classes, list):
                require(
                    host_classes[0] == "atlas-composition-host",
                    f"compositions[{index}].host_classes must start with "
                    "atlas-composition-host",
                    errors,
                )
                require(
                    host_classes[-1] == f"atlas-composition--{name}",
                    f"compositions[{index}].variant class must match the name",
                    errors,
                )
            density = composition.get("density", {})
            require(
                isinstance(density, dict),
                f"compositions[{index}].density must be an object",
                errors,
            )
            if isinstance(density, dict):
                require(
                    set(density) == {"min", "max", "reduced", "area_divisor"},
                    f"compositions[{index}].density keys are invalid",
                    errors,
                )
                for key in ("min", "max", "reduced", "area_divisor"):
                    require(
                        isinstance(density.get(key), int) and density[key] > 0,
                        f"compositions[{index}].density.{key} must be a "
                        "positive integer",
                        errors,
                    )
                if all(
                    isinstance(density.get(key), int)
                    for key in ("reduced", "min", "max")
                ):
                    require(
                        density["reduced"] <= density["min"] <= density["max"],
                        f"compositions[{index}].density order is invalid",
                        errors,
                    )
            breaks = composition.get("domain_breaks", [])
            require(
                isinstance(breaks, list) and len(breaks) == 2,
                f"compositions[{index}].domain_breaks is invalid",
                errors,
            )
            if (
                isinstance(breaks, list)
                and len(breaks) == 2
                and all(_is_number(value) for value in breaks)
            ):
                require(
                    0 < breaks[0] < breaks[1] < 1,
                    f"compositions[{index}].domain_breaks must be "
                    "ascending fractions",
                    errors,
                )
            styles = composition.get("domain_styles", [])
            require(
                isinstance(styles, list) and len(styles) == 3,
                f"compositions[{index}].domain_styles is invalid",
                errors,
            )
            if isinstance(styles, list):
                for style in styles:
                    require(
                        isinstance(style, str) and style.startswith("rgba("),
                        f"compositions[{index}].domain_styles must use rgba values",
                        errors,
                    )
            light = composition.get("light", {})
            require(
                isinstance(light, dict),
                f"compositions[{index}].light must be an object",
                errors,
            )
            if isinstance(light, dict):
                require(
                    set(light) == {"radius_min", "radius_ratio", "smoothing"},
                    f"compositions[{index}].light keys are invalid",
                    errors,
                )
                require(
                    isinstance(light.get("radius_min"), int)
                    and light["radius_min"] > 0,
                    f"compositions[{index}].light.radius_min is invalid",
                    errors,
                )
                for key in ("radius_ratio", "smoothing"):
                    require(
                        _is_number(light.get(key)) and light[key] > 0,
                        f"compositions[{index}].light.{key} is invalid",
                        errors,
                    )
            for key in ("visual_contract", "evidence_contract"):
                require(
                    isinstance(composition.get(key), str) and bool(composition[key]),
                    f"compositions[{index}].{key} is required",
                    errors,
                )

    requirements = document.get("validation_requirements", [])
    require(
        isinstance(requirements, list) and len(requirements) >= 5,
        "validation requirements are incomplete",
        errors,
    )
    for requirement in requirements if isinstance(requirements, list) else []:
        require(isinstance(requirement, str) and bool(requirement), "validation requirements must be non-empty strings", errors)

    return ValidationResult(tuple(errors), fingerprint)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalogue",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "policy/atlasfield-composition-catalogue.json",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    try:
        document = load_json(args.catalogue)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result = validate_catalogue(document)
    if not args.quiet:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        if result.fingerprint:
            print(f"AtlasField catalogue fingerprint: {result.fingerprint}")
        print("PASS" if result.ok else "FAIL")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
