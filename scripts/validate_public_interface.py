#!/usr/bin/env python3
"""Validate Atlas Systems public interface policy and repository manifests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CONTRACT_SCHEMA = "atlas-control-plane/public-interface-contract/v1"
DOMAINS_SCHEMA = "atlas-control-plane/atlas-owned-domains/v1"
SURFACE_SCHEMA = "atlas-control-plane/public-interface-surface/v1"
REQUIRED_GLOBAL_ROUTES = ("Work", "Writing", "Lab", "About")
REQUIRED_STATUS_FIELDS = (
    "estate.operational",
    "estate.total_components",
    "estate.checked_at",
)
REQUIRED_STATUS_LABELS = {
    "initial": "checking",
    "all_operational": "nominal",
    "partial_majority_operational": "degraded",
    "half_or_fewer_operational": "unavailable",
    "missing_invalid_failed_or_stale": "unknown",
}
REQUIRED_ICON_FILES = {
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "site.webmanifest",
}
REQUIRED_METADATA = {
    "title",
    "description",
    "canonical",
    "theme-color",
    "icons",
    "og:type",
    "og:title",
    "og:description",
    "og:url",
    "og:site_name",
    "og:image",
    "og:image:width",
    "og:image:height",
    "og:image:alt",
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
}
ALLOWED_KINDS = {
    "homepage",
    "standard",
    "lab-home",
    "lab-tool",
    "article",
    "status",
    "cv",
    "product",
    "api-docs",
    "error",
}
ALLOWED_INDEXING = {"index", "noindex, follow", "noindex, nofollow"}
ALLOWED_STATUS = {"homepage-owned", "aggregate-link", "none"}


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_domains(doc: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    require(doc.get("schema_version") == DOMAINS_SCHEMA, "domains schema_version is invalid", errors)
    require(doc.get("status") == "accepted", "domains policy is not accepted", errors)

    domains = doc.get("domains")
    require(isinstance(domains, list) and bool(domains), "domains must be a non-empty list", errors)
    hosts: list[str] = []
    if isinstance(domains, list):
        for index, item in enumerate(domains):
            require(isinstance(item, dict), f"domains[{index}] must be an object", errors)
            if not isinstance(item, dict):
                continue
            host = item.get("host")
            require(isinstance(host, str) and host == host.lower(), f"domains[{index}].host must be lowercase", errors)
            require(isinstance(host, str) and host.endswith("atlas-systems.uk"), f"domains[{index}].host is outside Atlas Systems", errors)
            if isinstance(host, str):
                hosts.append(host)
            paths = item.get("human_html_paths")
            require(isinstance(paths, list) and bool(paths), f"domains[{index}].human_html_paths must be non-empty", errors)
            if isinstance(paths, list):
                for path in paths:
                    require(isinstance(path, str) and path.startswith("/"), f"domains[{index}] contains an invalid path", errors)

    require(hosts == sorted(hosts), "domains must be sorted by host", errors)
    require(len(hosts) == len(set(hosts)), "domains must be unique", errors)

    rules = doc.get("rules")
    require(isinstance(rules, dict), "domains rules must be an object", errors)
    if isinstance(rules, dict):
        require(rules.get("atlas_owned_html_target") == "same-tab", "Atlas-owned HTML must remain same-tab", errors)
        require(rules.get("external_target") == "new-tab", "external links must use new-tab", errors)
        require(set(rules.get("external_rel", [])) == {"noopener", "noreferrer"}, "external_rel must contain noopener and noreferrer", errors)

    return ValidationResult(tuple(errors))


def validate_contract(doc: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    require(doc.get("schema_version") == CONTRACT_SCHEMA, "contract schema_version is invalid", errors)
    require(doc.get("status") == "accepted", "interface contract is not accepted", errors)

    baseline = doc.get("baseline", {})
    require(baseline.get("accessibility") == "WCAG 2.2 AA", "WCAG 2.2 AA must be the baseline", errors)
    require(baseline.get("runtime_assets") == "repository-local", "runtime assets must be repository-local", errors)
    require(baseline.get("free_tier_required") is True, "free-tier compatibility must be required", errors)

    header = doc.get("global_header", {})
    labels = tuple(item.get("label") for item in header.get("routes", []) if isinstance(item, dict))
    require(labels == REQUIRED_GLOBAL_ROUTES, "global routes must be Work, Writing, Lab, About in order", errors)
    require(header.get("search_required") is True, "global search must be required", errors)
    require(header.get("non_home_status_required") is True, "non-home status must be required", errors)
    require(header.get("homepage_duplicate_status_forbidden") is True, "homepage duplicate status must be forbidden", errors)

    status = doc.get("status_indicator", {})
    require(status.get("source") == "https://api.atlas-systems.uk/v1/stats", "status source must be /v1/stats", errors)
    require(tuple(status.get("fields", [])) == REQUIRED_STATUS_FIELDS, "status fields are invalid or out of order", errors)
    require(status.get("stale_after_seconds") == 1200, "status stale threshold must remain 1200 seconds", errors)
    require(status.get("link") == "https://status.atlas-systems.uk/", "status link is invalid", errors)
    require(status.get("labels") == REQUIRED_STATUS_LABELS, "status labels are invalid", errors)
    require(status.get("aria_live") == "off", "header status must not become a live region", errors)

    search = doc.get("estate_search", {})
    require(search.get("production_primary_endpoint") == "https://api.atlas-systems.uk/v1/search", "search must use the bounded public API", errors)
    require(search.get("runtime_distribution") == "versioned-repository-local-copy", "search assets must be local copies", errors)
    require(search.get("remote_shared_script_forbidden") is True, "remote shared scripts must remain forbidden", errors)

    icons = doc.get("browser_icons", {})
    require(set(icons.get("required_files", [])) == REQUIRED_ICON_FILES, "browser icon file set is incomplete", errors)
    require(icons.get("local_copy_required") is True, "browser icons must be local", errors)

    metadata = doc.get("metadata", {})
    require(set(metadata.get("required", [])) == REQUIRED_METADATA, "metadata field set is incomplete", errors)
    require(metadata.get("cv_robots") == "noindex, follow", "CV robots policy must be noindex, follow", errors)
    require(metadata.get("error_page_robots") == "noindex, nofollow", "error-page robots policy must fail closed", errors)

    readability = doc.get("readability", {})
    require(readability.get("long_form_body_font_px") == 15, "long-form body font must be 15px", errors)
    require(readability.get("long_form_line_height") == 1.8, "long-form line height must be 1.8", errors)
    require(readability.get("long_form_max_width_px") == 720, "long-form maximum width must be 720px", errors)

    generated = doc.get("generated_content", {})
    require(generated.get("article_generator") == "AtlasReaper311/atlas-article-gen", "article generator ownership is invalid", errors)
    require(generated.get("publisher") == "AtlasReaper311/atlas-scheduler", "publisher ownership is invalid", errors)
    require(generated.get("hand_edit_generated_article_html_forbidden") is True, "generated article hand edits must remain forbidden", errors)

    return ValidationResult(tuple(errors))


def validate_surface_manifest(doc: dict[str, Any], root: Path) -> ValidationResult:
    errors: list[str] = []
    require(doc.get("schema_version") == SURFACE_SCHEMA, "surface manifest schema_version is invalid", errors)
    repository = doc.get("repository")
    require(isinstance(repository, str) and repository.startswith("AtlasReaper311/"), "surface manifest repository is invalid", errors)
    surfaces = doc.get("surfaces")
    require(isinstance(surfaces, list) and bool(surfaces), "surface manifest must contain surfaces", errors)
    if not isinstance(surfaces, list):
        return ValidationResult(tuple(errors))

    urls: list[str] = []
    for index, surface in enumerate(surfaces):
        prefix = f"surfaces[{index}]"
        require(isinstance(surface, dict), f"{prefix} must be an object", errors)
        if not isinstance(surface, dict):
            continue

        url = surface.get("url")
        parsed = urlparse(url) if isinstance(url, str) else None
        require(bool(parsed and parsed.scheme == "https" and parsed.netloc), f"{prefix}.url must be an HTTPS URL", errors)
        if isinstance(url, str):
            urls.append(url)

        source = surface.get("source")
        require(isinstance(source, str) and bool(source), f"{prefix}.source is required", errors)
        if isinstance(source, str):
            require((root / source).exists(), f"{prefix}.source does not exist: {source}", errors)

        kind = surface.get("kind")
        require(kind in ALLOWED_KINDS, f"{prefix}.kind is invalid", errors)
        indexing = surface.get("indexing")
        require(indexing in ALLOWED_INDEXING, f"{prefix}.indexing is invalid", errors)
        require(surface.get("global_header") is True, f"{prefix} must declare the global header", errors)
        require(surface.get("search") is True, f"{prefix} must declare estate search", errors)
        require(surface.get("status_indicator") in ALLOWED_STATUS, f"{prefix}.status_indicator is invalid", errors)
        if kind == "homepage":
            require(surface.get("status_indicator") == "homepage-owned", f"{prefix} homepage must own its status treatment", errors)
        else:
            require(surface.get("status_indicator") == "aggregate-link", f"{prefix} non-home surface must use aggregate-link", errors)
        if kind == "cv":
            require(indexing == "noindex, follow", f"{prefix} CV indexing must be noindex, follow", errors)
        if kind == "error":
            require(indexing == "noindex, nofollow", f"{prefix} error indexing must be noindex, nofollow", errors)
        if kind == "lab-home":
            require(surface.get("contextual_navigation") is True, f"{prefix} Lab home must declare contextual navigation", errors)

        require(REQUIRED_ICON_FILES.issubset(set(surface.get("icons", []))), f"{prefix} icon declarations are incomplete", errors)
        require(REQUIRED_METADATA.issubset(set(surface.get("metadata", []))), f"{prefix} metadata declarations are incomplete", errors)
        require(surface.get("link_policy") == "atlas-owned-same-tab-external-safe-new-tab", f"{prefix} link policy is invalid", errors)
        require(isinstance(surface.get("footer"), str) and bool(surface.get("footer")), f"{prefix}.footer is required", errors)

    require(len(urls) == len(set(urls)), "surface URLs must be unique", errors)
    return ValidationResult(tuple(errors))


def validate(root: Path, manifest: Path | None) -> ValidationResult:
    errors: list[str] = []
    try:
        contract = load_json(root / "policy/public-interface-contract.json")
        domains = load_json(root / "policy/atlas-owned-domains.json")
    except ValueError as exc:
        return ValidationResult((str(exc),))

    errors.extend(validate_contract(contract).errors)
    errors.extend(validate_domains(domains).errors)

    if manifest is not None:
        try:
            surface_doc = load_json(manifest)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            errors.extend(validate_surface_manifest(surface_doc, manifest.parent.parent if manifest.parent.name == ".atlas" else root).errors)

    return ValidationResult(tuple(errors))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="atlas-infra repository root")
    parser.add_argument("--manifest", type=Path, help="optional repository .atlas/public-interface.json")
    parser.add_argument("--report", type=Path, help="optional JSON report output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = validate(args.root.resolve(), args.manifest.resolve() if args.manifest else None)
    report = {"ok": result.ok, "errors": list(result.errors)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not result.ok:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Public interface contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
