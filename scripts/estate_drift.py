#!/usr/bin/env python3
"""Validate estate drift against current Atlas Infra classification authority.

The validator reuses the Phase 1.4 snapshot model and the owning public
repository classification projection. GitHub owner listing and atlas-api-public
topology remain observation inputs. Missing observation stays
UNKNOWN / NOT OBSERVED and is not treated as conformance. The report does not
prove deployment, runtime, or live verification.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from control_plane_contracts import sha256_hex, validate_instance
import estate_snapshot
import public_repository_classifications

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = estate_snapshot.DEFAULT_REGISTRY
DEFAULT_SUPPLEMENT = estate_snapshot.DEFAULT_SUPPLEMENT
DEFAULT_PROJECTION = estate_snapshot.DEFAULT_PROJECTION
DEFAULT_SCHEMA = ROOT / "policy" / "estate-drift.schema.json"
DEFAULT_JSON = ROOT / "reports" / "estate-drift.json"
DEFAULT_MARKDOWN = ROOT / "reports" / "estate-drift.md"
SCHEMA_VERSION = "atlas-estate-drift/report/v1"
AUTHORITY = estate_snapshot.AUTHORITY
UNKNOWN = estate_snapshot.UNKNOWN
CLASSIFICATION_AUTHORITY = (
    "policy/estate-registry.json and policy/public-assurance-repositories.json"
)
PROJECTION_SOURCE = "policy/public-repository-classifications.json"
CLASS_KINDS = (
    "owned-public-missing-classification",
    "projection-differs-from-authority",
    "presentation-conflicts-with-classification",
    "hand-maintained-current-truth-conflict",
    "duplicate-or-ambiguous-ownership",
)
CLASSIFICATION_AXES = ("lifecycle", "scope", "provenance")
CURRENT_TRUTH_CONTRACTS = (
    {
        "path": "policy/estate-registry.json",
        "field": "approved_repository_count",
        "kind": "hand-maintained-current-truth-conflict",
    },
)
NON_CURRENT_TRUTH_PATHS = (
    "docs/2026-completion-roadmap.md",
    "docs/evidence-lifecycle-architecture-task.md",
    "docs/agent-conventions.md",
    "tests/fixtures/",
    "scripts/tests/",
)


class EstateDriftError(ValueError):
    """Raised when drift inputs or generated reports are malformed."""


def load_object(path: Path) -> dict[str, Any]:
    return estate_snapshot.load_object(path)


def is_current_truth_path(path: str) -> bool:
    relative = path.replace("\\", "/")
    if any(relative == item or relative.startswith(item) for item in NON_CURRENT_TRUTH_PATHS):
        return False
    return any(relative == item["path"] for item in CURRENT_TRUTH_CONTRACTS)


def _finding(
    *,
    kind: str,
    subject: str,
    authoritative_source: str,
    observed_source: str,
    reason: str,
    result_class: str,
) -> dict[str, str]:
    return {
        "kind": kind,
        "subject": subject,
        "authoritative_source": authoritative_source,
        "observed_source": observed_source,
        "reason": reason,
        "result_class": result_class,
    }


def _repository_names(values: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(values, list):
        return names
    for item in values:
        if isinstance(item, dict) and isinstance(item.get("repository"), str):
            names.append(item["repository"])
    return names


def _authority_names(registry: dict[str, Any], supplement: dict[str, Any]) -> list[str]:
    return _repository_names(registry.get("repositories")) + _repository_names(
        supplement.get("repositories")
    )


def _classification_map(projection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classified: dict[str, dict[str, Any]] = {}
    for item in projection.get("repositories") or []:
        if isinstance(item, dict) and isinstance(item.get("repository"), str):
            classified[item["repository"]] = item
    return classified


def _is_public_github(item: dict[str, Any]) -> bool:
    if item.get("private") is True:
        return False
    visibility = item.get("visibility")
    return isinstance(visibility, str) and visibility.casefold() == "public"


def collect_identity_ambiguity(
    registry: dict[str, Any], supplement: dict[str, Any]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    runtime = _repository_names(registry.get("repositories"))
    extra = _repository_names(supplement.get("repositories"))

    def duplicates(names: list[str], source: str) -> None:
        seen: dict[str, int] = {}
        for name in names:
            seen[name] = seen.get(name, 0) + 1
        for name, count in sorted(seen.items()):
            if count > 1:
                findings.append(
                    _finding(
                        kind="duplicate-or-ambiguous-ownership",
                        subject=name,
                        authoritative_source=source,
                        observed_source=source,
                        reason=(
                            "duplicate repository identity appears in committed "
                            "classification authority; no winner was chosen."
                        ),
                        result_class="deterministic-drift",
                    )
                )

    duplicates(runtime, "policy/estate-registry.json")
    duplicates(extra, "policy/public-assurance-repositories.json")

    runtime_set = set(runtime)
    for name in sorted(set(extra) & runtime_set):
        findings.append(
            _finding(
                kind="duplicate-or-ambiguous-ownership",
                subject=name,
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=CLASSIFICATION_AUTHORITY,
                reason=(
                    "runtime registry and public-assurance supplement both claim "
                    "this repository; no winner was chosen."
                ),
                result_class="deterministic-drift",
            )
        )

    folded: dict[str, list[str]] = defaultdict(list)
    for name in runtime + extra:
        key = name.casefold()
        if name not in folded[key]:
            folded[key].append(name)
    for names in folded.values():
        if len(names) > 1:
            subject = ",".join(sorted(names))
            findings.append(
                _finding(
                    kind="duplicate-or-ambiguous-ownership",
                    subject=subject,
                    authoritative_source=CLASSIFICATION_AUTHORITY,
                    observed_source=CLASSIFICATION_AUTHORITY,
                    reason=(
                        "repository identities differ only by case and cannot "
                        "share one deterministic classification."
                    ),
                    result_class="deterministic-drift",
                )
            )
    return findings


def collect_projection_drift(
    registry: dict[str, Any],
    supplement: dict[str, Any],
    committed_text: str,
    projection_source: str,
) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    try:
        built = public_repository_classifications.build_projection(registry, supplement)
    except public_repository_classifications.ClassificationProjectionError as error:
        message = str(error)
        kind = (
            "duplicate-or-ambiguous-ownership"
            if "duplicate" in message or "overlap" in message
            else "malformed-authority-or-snapshot"
        )
        findings.append(
            _finding(
                kind=kind,
                subject=PROJECTION_SOURCE,
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=projection_source,
                reason=message,
                result_class="deterministic-drift",
            )
        )
        return None, findings

    rendered = public_repository_classifications.render_json(built)
    if committed_text != rendered:
        findings.append(
            _finding(
                kind="projection-differs-from-authority",
                subject=PROJECTION_SOURCE,
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=projection_source,
                reason=(
                    "committed classification projection does not match the "
                    "owning generator output."
                ),
                result_class="deterministic-drift",
            )
        )
    return built, findings


def collect_github_public_missing(
    *,
    github_repositories: dict[str, dict[str, Any]] | None,
    github_source: str,
    authority_names: set[str],
) -> list[dict[str, str]]:
    if github_repositories is None:
        return [
            _finding(
                kind="owned-public-missing-classification",
                subject="github-observation",
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=UNKNOWN,
                reason=(
                    "GitHub owner observation was not supplied, so owned public "
                    "repositories cannot be checked for missing classification."
                ),
                result_class=UNKNOWN,
            )
        ]
    findings: list[dict[str, str]] = []
    for name in sorted(github_repositories):
        item = github_repositories[name]
        if not _is_public_github(item):
            continue
        if name in authority_names:
            continue
        findings.append(
            _finding(
                kind="owned-public-missing-classification",
                subject=name,
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=github_source,
                reason=(
                    "owned public GitHub repository has no Atlas Infra "
                    "classification authority."
                ),
                result_class="observation-derived-drift",
            )
        )
    return findings


def collect_presentation_conflicts(
    *,
    presentation: dict[str, Any] | None,
    presentation_source: str,
    classified: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    if presentation is None:
        return [
            _finding(
                kind="presentation-conflicts-with-classification",
                subject="presentation",
                authoritative_source=CLASSIFICATION_AUTHORITY,
                observed_source=UNKNOWN,
                reason=(
                    "presentation or topology observation was not supplied, so "
                    "classification claims in atlas-api-public cannot be compared."
                ),
                result_class=UNKNOWN,
            )
        ]
    findings: list[dict[str, str]] = []
    repositories_field = presentation.get("repositories")
    if isinstance(repositories_field, list):
        for index, item in enumerate(repositories_field):
            if not isinstance(item, dict):
                continue
            claimed = {
                axis: item.get(axis) for axis in CLASSIFICATION_AXES if axis in item
            }
            if not claimed:
                continue
            subject = item.get("repository")
            if not isinstance(subject, str):
                subject = f"{presentation_source}:repositories[{index}]"
            findings.append(
                _finding(
                    kind="presentation-conflicts-with-classification",
                    subject=subject,
                    authoritative_source=CLASSIFICATION_AUTHORITY,
                    observed_source=presentation_source,
                    reason=(
                        "presentation repositories array is not classification "
                        "authority and carries lifecycle, scope, or provenance claims."
                    ),
                    result_class="observation-derived-drift",
                )
            )
    for item in presentation.get("components") or []:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            continue
        repo_name = estate_snapshot.github_full_name(
            item.get("repo") if isinstance(item.get("repo"), str) else None
        )
        if repo_name is None:
            continue
        claims = {
            axis: item[axis]
            for axis in CLASSIFICATION_AXES
            if axis in item and isinstance(item.get(axis), str)
        }
        if not claims:
            continue
        authority = classified.get(repo_name)
        if authority is None:
            findings.append(
                _finding(
                    kind="presentation-conflicts-with-classification",
                    subject=f"{repo_name}:{item['name']}",
                    authoritative_source=CLASSIFICATION_AUTHORITY,
                    observed_source=presentation_source,
                    reason=(
                        "presentation names a repository that has no Atlas Infra "
                        "classification; presentation was not used as authority."
                    ),
                    result_class="observation-derived-drift",
                )
            )
            continue
        for axis, presented in claims.items():
            expected = authority.get(axis)
            if presented != expected:
                findings.append(
                    _finding(
                        kind="presentation-conflicts-with-classification",
                        subject=f"{repo_name}:{item['name']}:{axis}",
                        authoritative_source=CLASSIFICATION_AUTHORITY,
                        observed_source=presentation_source,
                        reason=(
                            f"presentation {axis} `{presented}` disagrees with "
                            f"Atlas Infra `{expected}` and is not classification authority."
                        ),
                        result_class="observation-derived-drift",
                    )
                )
    return findings


def collect_hand_maintained_conflicts(registry: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    runtime = registry.get("repositories")
    approved = registry.get("approved_repository_count")
    runtime_count = len(runtime) if isinstance(runtime, list) else None
    if not isinstance(approved, int) or runtime_count is None:
        findings.append(
            _finding(
                kind="malformed-authority-or-snapshot",
                subject="policy/estate-registry.json",
                authoritative_source="policy/estate-registry.json",
                observed_source="policy/estate-registry.json",
                reason="approved_repository_count or repositories list is malformed.",
                result_class="deterministic-drift",
            )
        )
        return findings
    if approved != runtime_count:
        findings.append(
            _finding(
                kind="hand-maintained-current-truth-conflict",
                subject="policy/estate-registry.json",
                authoritative_source="policy/estate-registry.json repositories list",
                observed_source="policy/estate-registry.json approved_repository_count",
                reason=(
                    "hand-maintained approved_repository_count disagrees with the "
                    f"runtime registry list length ({approved} vs {runtime_count})."
                ),
                result_class="deterministic-drift",
            )
        )
    return findings


def _class_status(findings: list[dict[str, str]], kind: str) -> dict[str, Any]:
    matched = [item for item in findings if item["kind"] == kind]
    if any(item["result_class"] == UNKNOWN for item in matched) and not any(
        item["result_class"] != UNKNOWN for item in matched
    ):
        status = UNKNOWN
    elif matched:
        status = "disagree"
    else:
        status = "agree"
    return {"status": status, "finding_count": len(matched)}


def _dedupe(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    unique: dict[str, dict[str, str]] = {}
    for item in findings:
        key = json.dumps(item, sort_keys=True, separators=(",", ":"))
        unique[key] = item
    return sorted(
        unique.values(),
        key=lambda item: (
            item["kind"],
            item["subject"],
            item["result_class"],
            item["reason"],
        ),
    )


def deterministic_payload(report: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(report))
    clone.get("observation", {}).pop("generated_at", None)
    clone.pop("content_fingerprint", None)
    return clone


def build_report(
    *,
    registry: dict[str, Any],
    supplement: dict[str, Any],
    committed_projection_text: str,
    github_repositories: dict[str, dict[str, Any]] | None,
    github_route: str,
    github_source: str,
    presentation: dict[str, Any] | None,
    presentation_source: str,
    generated_at: str,
    source_commit: str,
    projection_source: str = PROJECTION_SOURCE,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    findings.extend(collect_identity_ambiguity(registry, supplement))
    built, projection_findings = collect_projection_drift(
        registry, supplement, committed_projection_text, projection_source
    )
    findings.extend(projection_findings)
    findings.extend(collect_hand_maintained_conflicts(registry))
    findings.extend(
        collect_github_public_missing(
            github_repositories=github_repositories,
            github_source=github_source,
            authority_names=set(_authority_names(registry, supplement)),
        )
    )

    classified = _classification_map(built) if built is not None else {}
    if built is None:
        for item in (registry.get("repositories") or []) + (
            supplement.get("repositories") or []
        ):
            if isinstance(item, dict) and isinstance(item.get("repository"), str):
                classified.setdefault(item["repository"], item)
    findings.extend(
        collect_presentation_conflicts(
            presentation=presentation,
            presentation_source=presentation_source,
            classified=classified,
        )
    )

    snapshot = None
    snapshot_fingerprint = UNKNOWN
    source_fingerprint = UNKNOWN
    if built is not None:
        source_fingerprint = built.get("source_fingerprint", UNKNOWN)
        try:
            snapshot = estate_snapshot.build_snapshot(
                registry=registry,
                supplement=supplement,
                projection=built,
                github_repositories=github_repositories,
                github_route=github_route,
                presentation=presentation,
                presentation_source=presentation_source,
                generated_at=generated_at,
                source_commit=source_commit,
            )
            snapshot_fingerprint = snapshot["content_fingerprint"]
        except (
            estate_snapshot.EstateSnapshotError,
            public_repository_classifications.ClassificationProjectionError,
        ) as error:
            findings.append(
                _finding(
                    kind="malformed-authority-or-snapshot",
                    subject="estate-snapshot",
                    authoritative_source=CLASSIFICATION_AUTHORITY,
                    observed_source="scripts/estate_snapshot.py",
                    reason=str(error),
                    result_class="deterministic-drift",
                )
            )

    findings = _dedupe(findings)
    classes = {kind: _class_status(findings, kind) for kind in CLASS_KINDS}
    deterministic = sum(
        1 for item in findings if item["result_class"] == "deterministic-drift"
    )
    observation_derived = sum(
        1 for item in findings if item["result_class"] == "observation-derived-drift"
    )
    unknown = sum(1 for item in findings if item["result_class"] == UNKNOWN)
    body = {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "observation": {
            "generated_at": estate_snapshot.validate_generated_at(generated_at),
            "source_commit": source_commit,
            "github": {
                "status": "observed" if github_repositories is not None else UNKNOWN,
                "route": github_route,
                "owner": estate_snapshot.DEFAULT_OWNER,
                "source": github_source,
            },
            "presentation": {
                "status": "observed" if presentation is not None else UNKNOWN,
                "source": presentation_source,
            },
            "classification": {
                "runtime_registry": "policy/estate-registry.json",
                "public_non_runtime": "policy/public-assurance-repositories.json",
                "projection": PROJECTION_SOURCE,
                "source_fingerprint": source_fingerprint,
            },
            "snapshot_content_fingerprint": snapshot_fingerprint,
        },
        "classes": classes,
        "findings": findings,
        "summary": {
            "deterministic_drift": deterministic,
            "observation_derived_drift": observation_derived,
            "unknown_not_observed": unknown,
            "blocking": bool(deterministic or observation_derived),
        },
        "evidence_boundary": estate_snapshot.EVIDENCE_BOUNDARY,
    }
    body["content_fingerprint"] = "sha256:" + sha256_hex(deterministic_payload(body))
    return body


def validate_report(report: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = validate_instance(report, schema)
    if errors:
        raise EstateDriftError(errors[0])
    expected = "sha256:" + sha256_hex(deterministic_payload(report))
    if report.get("content_fingerprint") != expected:
        raise EstateDriftError("content fingerprint does not match deterministic drift content")


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    observation = report["observation"]
    summary = report["summary"]
    lines = [
        "# Atlas Systems estate drift",
        "",
        f"Authority: `{report['authority']}`",
        "",
        "This report compares Atlas Infra classification authority, the owning "
        "deterministic projection, generated estate snapshot truth, and optional "
        "GitHub or presentation observation. It does not prove "
        "`DEPLOYMENT OBSERVED`, `DEPLOYED`, `RUNTIME VERIFIED`, or `LIVE VERIFIED`. "
        "Missing later evidence remains `UNKNOWN / NOT OBSERVED`.",
        "",
        "## Observation",
        "",
        f"- Generated at: `{observation['generated_at']}`",
        f"- Source commit: `{observation['source_commit']}`",
        f"- GitHub: `{observation['github']['status']}` from `{observation['github']['source']}`",
        f"- Presentation: `{observation['presentation']['status']}` from `{observation['presentation']['source']}`",
        f"- Classification fingerprint: `{observation['classification']['source_fingerprint']}`",
        f"- Snapshot fingerprint: `{observation['snapshot_content_fingerprint']}`",
        f"- Content fingerprint: `{report['content_fingerprint']}`",
        "",
        "## Classes",
        "",
    ]
    for kind in CLASS_KINDS:
        item = report["classes"][kind]
        lines.append(
            f"- `{kind}`: `{item['status']}` ({item['finding_count']} findings)"
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Deterministic drift: **{summary['deterministic_drift']}**",
            f"- Observation-derived drift: **{summary['observation_derived_drift']}**",
            f"- `UNKNOWN / NOT OBSERVED`: **{summary['unknown_not_observed']}**",
            f"- Blocking: `{'yes' if summary['blocking'] else 'no'}`",
            "",
            "## Findings",
            "",
        ]
    )
    if report["findings"]:
        for item in report["findings"]:
            lines.append(
                f"- `{item['kind']}` `{item['subject']}` [{item['result_class']}]: "
                f"{item['reason']} (authority `{item['authoritative_source']}`; "
                f"observed `{item['observed_source']}`)"
            )
    else:
        lines.append("None.")
    boundary = report["evidence_boundary"]
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            f"- Delivery stage claimed: `{boundary['delivery_stage_claimed']}`",
            f"- Later stage observation: `{boundary['later_stage_observation']}`",
            "- Does not prove: "
            + ", ".join(f"`{item}`" for item in boundary["does_not_prove"]),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(render_json(report), encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")


def build_from_paths(
    *,
    root: Path,
    registry_path: Path,
    supplement_path: Path,
    projection_path: Path,
    github_observation: Path | None,
    discover_github: bool,
    token_env: str,
    presentation_path: Path | None,
    generated_at: str,
    source_commit: str | None,
) -> dict[str, Any]:
    if github_observation is not None and discover_github:
        raise EstateDriftError("use either --github-observation or --discover-github, not both")
    registry = load_object(registry_path)
    supplement = load_object(supplement_path)
    committed_text = projection_path.read_text(encoding="utf-8")
    github_repositories: dict[str, dict[str, Any]] | None = None
    github_route = estate_snapshot.GITHUB_ROUTE
    github_source = UNKNOWN
    if github_observation is not None:
        github_repositories, recorded_route = estate_snapshot.load_github_observation(
            github_observation
        )
        github_route = recorded_route or (
            f"recorded-observation:{estate_snapshot.relative_source(github_observation, root)}"
        )
        github_source = estate_snapshot.relative_source(github_observation, root)
    elif discover_github:
        token = os.environ.get(token_env, "") or os.environ.get("GITHUB_TOKEN", "")
        github_repositories = estate_snapshot.list_owned_github_repositories(token)
        github_source = estate_snapshot.GITHUB_ROUTE
    presentation = (
        estate_snapshot.load_presentation(presentation_path)
        if presentation_path
        else None
    )
    presentation_source = (
        estate_snapshot.relative_source(presentation_path, root)
        if presentation_path
        else UNKNOWN
    )
    return build_report(
        registry=registry,
        supplement=supplement,
        committed_projection_text=committed_text,
        github_repositories=github_repositories,
        github_route=github_route,
        github_source=github_source,
        presentation=presentation,
        presentation_source=presentation_source,
        generated_at=generated_at,
        source_commit=estate_snapshot.resolve_source_commit(source_commit, root),
        projection_source=estate_snapshot.relative_source(projection_path, root),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Atlas estate drift from current authority and optional observation."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--supplement", type=Path, default=DEFAULT_SUPPLEMENT)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--github-observation", type=Path)
    parser.add_argument("--discover-github", action="store_true")
    parser.add_argument("--token-env", default="ATLAS_ESTATE_READ_TOKEN")
    parser.add_argument("--presentation", type=Path)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-at", type=str)
    parser.add_argument("--source-commit", type=str)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generated_at = args.generated_at or estate_snapshot.utc_now()
        report = build_from_paths(
            root=args.root,
            registry_path=args.registry,
            supplement_path=args.supplement,
            projection_path=args.projection,
            github_observation=args.github_observation,
            discover_github=args.discover_github,
            token_env=args.token_env,
            presentation_path=args.presentation,
            generated_at=generated_at,
            source_commit=args.source_commit,
        )
        schema = load_object(args.schema)
        validate_report(report, schema)
        if not args.discover_github:
            second = build_from_paths(
                root=args.root,
                registry_path=args.registry,
                supplement_path=args.supplement,
                projection_path=args.projection,
                github_observation=args.github_observation,
                discover_github=False,
                token_env=args.token_env,
                presentation_path=args.presentation,
                generated_at=report["observation"]["generated_at"],
                source_commit=report["observation"]["source_commit"],
            )
            if deterministic_payload(report) != deterministic_payload(second):
                raise EstateDriftError("drift report is not deterministic for identical inputs")
        if args.check:
            if args.json_out.is_file() or args.markdown_out.is_file():
                if not args.json_out.is_file() or not args.markdown_out.is_file():
                    raise EstateDriftError("drift outputs are incomplete")
                existing = json.loads(args.json_out.read_text(encoding="utf-8"))
                if deterministic_payload(existing) != deterministic_payload(report):
                    raise EstateDriftError(
                        "committed drift JSON differs from authoritative inputs"
                    )
                existing_markdown = args.markdown_out.read_text(encoding="utf-8")
                if existing_markdown != render_markdown(existing):
                    raise EstateDriftError(
                        "committed drift Markdown is not generated from the JSON model"
                    )
            blocking = report["summary"]["blocking"]
            print(
                "estate drift verified: "
                f"{report['summary']['deterministic_drift']} deterministic, "
                f"{report['summary']['observation_derived_drift']} observation-derived, "
                f"{report['summary']['unknown_not_observed']} unknown "
                f"({report['content_fingerprint']})"
            )
            return 2 if blocking else 0
        write_outputs(report, args.json_out, args.markdown_out)
        print(
            "estate drift written: "
            f"{report['summary']['deterministic_drift']} deterministic, "
            f"{report['summary']['observation_derived_drift']} observation-derived, "
            f"{report['summary']['unknown_not_observed']} unknown "
            f"({report['content_fingerprint']})"
        )
        return 2 if report["summary"]["blocking"] else 0
    except (
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        public_repository_classifications.ClassificationProjectionError,
        estate_snapshot.EstateSnapshotError,
    ) as error:
        print(f"estate drift failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
