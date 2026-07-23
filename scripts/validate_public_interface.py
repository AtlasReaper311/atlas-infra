#!/usr/bin/env python3
"""Validate Atlas Systems public interface policies and repository manifests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CONTRACT_SCHEMA = "atlas-control-plane/public-interface-contract/v1"
SYSTEM_SCHEMA = "atlas-control-plane/public-interface-system/v1"
DOMAINS_SCHEMA = "atlas-control-plane/atlas-owned-domains/v1"
SURFACE_SCHEMA = "atlas-control-plane/public-interface-surface/v1"

REQUIRED_GLOBAL_ROUTES = ("Work", "Writing", "Lab", "About")
REQUIRED_V2_GLOBAL_ROUTES = ("Work", "Writing", "Lab", "Systems", "About")
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
REQUIRED_VOCABULARY = {
    "project",
    "product",
    "service",
    "tool",
    "experiment",
    "interface",
    "case-study",
    "article",
    "repository",
    "merged",
    "deployed",
    "published",
}
REQUIRED_RUNTIME_STATES = (
    "operational",
    "degraded",
    "unavailable",
    "unknown",
)
REQUIRED_MATURITY_LABELS = (
    "Production",
    "Tool",
    "Experiment",
    "Preview",
    "Planned",
    "Retired",
)
REQUIRED_VIEWPORTS = (320, 375, 768, 1024, 1440)
REQUIRED_COMPONENT_ROLES = {
    "global-header",
    "product-strip",
    "page-introduction",
    "section-heading",
    "primary-action",
    "secondary-action",
    "text-action",
    "status-chip",
    "type-badge",
    "maturity-badge",
    "metric-grid",
    "standard-card",
    "editorial-card",
    "data-card",
    "interactive-card-frame",
    "tag-list",
    "filter-bar",
    "table-wrapper",
    "search-dialog",
    "loading-state",
    "empty-state",
    "unavailable-state",
    "unknown-state",
    "error-state",
    "footer",
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
    require(
        doc.get("schema_version") == DOMAINS_SCHEMA,
        "domains schema_version is invalid",
        errors,
    )
    require(doc.get("status") == "accepted", "domains policy is not accepted", errors)

    domains = doc.get("domains")
    require(
        isinstance(domains, list) and bool(domains),
        "domains must be a non-empty list",
        errors,
    )
    hosts: list[str] = []
    if isinstance(domains, list):
        for index, item in enumerate(domains):
            require(
                isinstance(item, dict),
                f"domains[{index}] must be an object",
                errors,
            )
            if not isinstance(item, dict):
                continue
            host = item.get("host")
            require(
                isinstance(host, str) and host == host.lower(),
                f"domains[{index}].host must be lowercase",
                errors,
            )
            require(
                isinstance(host, str) and host.endswith("atlas-systems.uk"),
                f"domains[{index}].host is outside Atlas Systems",
                errors,
            )
            if isinstance(host, str):
                hosts.append(host)
            paths = item.get("human_html_paths")
            require(
                isinstance(paths, list) and bool(paths),
                f"domains[{index}].human_html_paths must be non-empty",
                errors,
            )
            if isinstance(paths, list):
                for path in paths:
                    require(
                        isinstance(path, str) and path.startswith("/"),
                        f"domains[{index}] contains an invalid path",
                        errors,
                    )

    require(hosts == sorted(hosts), "domains must be sorted by host", errors)
    require(len(hosts) == len(set(hosts)), "domains must be unique", errors)

    rules = doc.get("rules")
    require(isinstance(rules, dict), "domains rules must be an object", errors)
    if isinstance(rules, dict):
        require(
            rules.get("atlas_owned_html_target") == "same-tab",
            "Atlas-owned HTML must remain same-tab",
            errors,
        )
        require(
            rules.get("external_target") == "new-tab",
            "external links must use new-tab",
            errors,
        )
        require(
            set(rules.get("external_rel", [])) == {"noopener", "noreferrer"},
            "external_rel must contain noopener and noreferrer",
            errors,
        )

    return ValidationResult(tuple(errors))


def validate_contract(doc: dict[str, Any]) -> ValidationResult:
    """Validate the currently deployed v1 shell contract."""

    errors: list[str] = []
    require(
        doc.get("schema_version") == CONTRACT_SCHEMA,
        "contract schema_version is invalid",
        errors,
    )
    require(
        doc.get("status") == "accepted",
        "interface contract is not accepted",
        errors,
    )

    baseline = doc.get("baseline", {})
    require(
        baseline.get("accessibility") == "WCAG 2.2 AA",
        "WCAG 2.2 AA must be the baseline",
        errors,
    )
    require(
        baseline.get("runtime_assets") == "repository-local",
        "runtime assets must be repository-local",
        errors,
    )
    require(
        baseline.get("free_tier_required") is True,
        "free-tier compatibility must be required",
        errors,
    )

    header = doc.get("global_header", {})
    labels = tuple(
        item.get("label")
        for item in header.get("routes", [])
        if isinstance(item, dict)
    )
    require(
        labels == REQUIRED_GLOBAL_ROUTES,
        "global routes must be Work, Writing, Lab, About in order",
        errors,
    )
    require(header.get("search_required") is True, "global search must be required", errors)
    require(
        header.get("non_home_status_required") is True,
        "non-home status must be required",
        errors,
    )
    require(
        header.get("homepage_duplicate_status_forbidden") is True,
        "homepage duplicate status must be forbidden",
        errors,
    )

    status = doc.get("status_indicator", {})
    require(
        status.get("source") == "https://api.atlas-systems.uk/v1/stats",
        "status source must be /v1/stats",
        errors,
    )
    require(
        tuple(status.get("fields", [])) == REQUIRED_STATUS_FIELDS,
        "status fields are invalid or out of order",
        errors,
    )
    require(
        status.get("stale_after_seconds") == 1200,
        "status stale threshold must remain 1200 seconds",
        errors,
    )
    require(
        status.get("link") == "https://status.atlas-systems.uk/",
        "status link is invalid",
        errors,
    )
    require(
        status.get("labels") == REQUIRED_STATUS_LABELS,
        "status labels are invalid",
        errors,
    )
    require(
        status.get("aria_live") == "off",
        "header status must not become a live region",
        errors,
    )

    search = doc.get("estate_search", {})
    require(
        search.get("production_primary_endpoint")
        == "https://api.atlas-systems.uk/v1/search",
        "search must use the bounded public API",
        errors,
    )
    require(
        search.get("runtime_distribution") == "versioned-repository-local-copy",
        "search assets must be local copies",
        errors,
    )
    require(
        search.get("remote_shared_script_forbidden") is True,
        "remote shared scripts must remain forbidden",
        errors,
    )

    icons = doc.get("browser_icons", {})
    require(
        set(icons.get("required_files", [])) == REQUIRED_ICON_FILES,
        "browser icon file set is incomplete",
        errors,
    )
    require(
        icons.get("local_copy_required") is True,
        "browser icons must be local",
        errors,
    )

    metadata = doc.get("metadata", {})
    require(
        set(metadata.get("required", [])) == REQUIRED_METADATA,
        "metadata field set is incomplete",
        errors,
    )
    require(
        metadata.get("cv_robots") == "noindex, follow",
        "CV robots policy must be noindex, follow",
        errors,
    )
    require(
        metadata.get("error_page_robots") == "noindex, nofollow",
        "error-page robots policy must fail closed",
        errors,
    )

    readability = doc.get("readability", {})
    require(
        readability.get("long_form_body_font_px") == 15,
        "long-form body font must be 15px",
        errors,
    )
    require(
        readability.get("long_form_line_height") == 1.8,
        "long-form line height must be 1.8",
        errors,
    )
    require(
        readability.get("long_form_max_width_px") == 720,
        "long-form maximum width must be 720px",
        errors,
    )

    generated = doc.get("generated_content", {})
    require(
        generated.get("article_generator") == "AtlasReaper311/atlas-article-gen",
        "article generator ownership is invalid",
        errors,
    )
    require(
        generated.get("publisher") == "AtlasReaper311/atlas-scheduler",
        "publisher ownership is invalid",
        errors,
    )
    require(
        generated.get("hand_edit_generated_article_html_forbidden") is True,
        "generated article hand edits must remain forbidden",
        errors,
    )

    return ValidationResult(tuple(errors))


def _route_labels(routes: Any) -> tuple[str | None, ...]:
    if not isinstance(routes, list):
        return ()
    return tuple(
        item.get("label") if isinstance(item, dict) else None
        for item in routes
    )


def validate_system(doc: dict[str, Any]) -> ValidationResult:
    """Validate the accepted v2 target without declaring migrations complete."""

    errors: list[str] = []
    require(
        doc.get("schema_version") == SYSTEM_SCHEMA,
        "system schema_version is invalid",
        errors,
    )
    require(doc.get("version") == "2.0.0", "system version must be 2.0.0", errors)
    require(doc.get("status") == "accepted", "interface system is not accepted", errors)

    authority = doc.get("authority", {})
    require(
        authority.get("decision")
        == "docs/adrs/ADR-0008-public-interface-system-v2.md",
        "system decision authority is invalid",
        errors,
    )
    require(
        authority.get("shell_contract") == "policy/public-interface-contract.json",
        "v1 shell authority must remain explicit during migration",
        errors,
    )
    require(
        authority.get("governance_repository") == "AtlasReaper311/atlas-infra",
        "system governance owner is invalid",
        errors,
    )
    implementation = authority.get("implementation_repository", {})
    require(
        implementation.get("repository") == "AtlasReaper311/atlas-interface-kit",
        "interface-kit repository name is invalid",
        errors,
    )
    require(
        implementation.get("state") in {"approved-not-created", "active"},
        "interface-kit state is invalid",
        errors,
    )

    migration = doc.get("migration", {})
    require(
        migration.get("state") in {
            "approved-source-only",
            "implementation",
            "rollout",
            "complete",
        },
        "migration state is invalid",
        errors,
    )
    require(
        migration.get("current_shell_contract_remains_active") is True,
        "current shell contract must remain active until migration",
        errors,
    )
    require(
        migration.get("production_rollout_requires_separate_approval") is True,
        "production rollout must require separate approval",
        errors,
    )
    expected_order = (
        "authority",
        "interface-kit",
        "atlas-systems",
        "generated-writing",
        "status",
        "atlas-api-public",
        "ramone-edge",
        "atlas-doc-viewer",
        "conformance",
    )
    require(
        tuple(migration.get("order", [])) == expected_order,
        "migration order is invalid",
        errors,
    )

    vocabulary = doc.get("vocabulary", {})
    definitions = vocabulary.get("definitions", {})
    require(
        isinstance(definitions, dict)
        and REQUIRED_VOCABULARY.issubset(definitions),
        "public vocabulary is incomplete",
        errors,
    )
    require(
        tuple(vocabulary.get("runtime_states", [])) == REQUIRED_RUNTIME_STATES,
        "runtime states must be operational, degraded, unavailable, unknown",
        errors,
    )
    require(
        vocabulary.get("initial_runtime_state") == "checking",
        "initial runtime state must be checking",
        errors,
    )
    require(
        tuple(vocabulary.get("maturity_labels", [])) == REQUIRED_MATURITY_LABELS,
        "maturity labels are invalid or out of order",
        errors,
    )
    require(
        vocabulary.get("maturity_is_separate_from_runtime_state") is True,
        "maturity and runtime state must remain separate",
        errors,
    )
    require(
        vocabulary.get("identifiers_remain_visible") is True,
        "public identifiers must remain visible",
        errors,
    )

    navigation = doc.get("navigation", {})
    require(
        _route_labels(navigation.get("global_routes"))
        == REQUIRED_V2_GLOBAL_ROUTES,
        "v2 global routes must be Work, Writing, Lab, Systems, About in order",
        errors,
    )
    desktop = navigation.get("desktop", {})
    require(
        desktop.get("left") == ["wordmark", "aggregate-status"],
        "desktop left zone must contain wordmark and aggregate status",
        errors,
    )
    require(
        desktop.get("centre") == ["global-routes"],
        "desktop centre zone must contain global routes",
        errors,
    )
    require(
        desktop.get("right") == ["estate-search"],
        "desktop right zone must contain estate search",
        errors,
    )
    require(
        desktop.get("status_display") == "state-only",
        "desktop status must use state-only presentation",
        errors,
    )
    require(
        desktop.get("status_healthy_label") == "Operational",
        "healthy public label must be Operational",
        errors,
    )
    require(
        desktop.get("status_link") == "https://status.atlas-systems.uk/",
        "desktop status must link directly to Status",
        errors,
    )
    require(
        desktop.get("status_action") == "direct-navigation",
        "desktop status action must be direct navigation",
        errors,
    )
    require(
        desktop.get("search_control") == "compact-button-with-shortcut",
        "desktop search must use the compact shortcut control",
        errors,
    )
    mobile = navigation.get("mobile", {})
    require(
        mobile.get("primary_navigation") == "bottom-navigation",
        "mobile navigation must use the bottom navigation",
        errors,
    )
    require(
        mobile.get("header") == ["wordmark", "aggregate-status", "search-icon"],
        "mobile header composition is invalid",
        errors,
    )
    require(
        mobile.get("active_route_required") is True,
        "mobile navigation must identify the active route",
        errors,
    )
    require(
        mobile.get("must_not_obscure_content_or_focus") is True,
        "mobile navigation must not obscure content or focus",
        errors,
    )

    systems = doc.get("systems_directory", {})
    require(
        systems.get("route") == "https://atlas-systems.uk/systems/",
        "Systems directory route is invalid",
        errors,
    )
    require(
        systems.get("groups")
        == ["Portfolio", "Products", "Engineering tools"],
        "Systems directory groups are invalid",
        errors,
    )
    require(
        systems.get("human_facing_primary") is True,
        "Systems must prioritise human-facing destinations",
        errors,
    )
    require(
        systems.get("machine_facing_access") == "secondary-detail",
        "machine-facing access must remain secondary detail",
        errors,
    )
    require(
        systems.get("private_components_as_context_only") is True,
        "private components must remain context-only",
        errors,
    )
    require(
        systems.get("selective_runtime_state") is True,
        "Systems runtime state must be selective",
        errors,
    )
    require(
        systems.get("simplified_architecture_diagram") is True,
        "Systems must include the simplified architecture diagram",
        errors,
    )
    require(
        systems.get("full_system_map_route")
        == "https://atlas-systems.uk/lab/system-map/",
        "full System Map route is invalid",
        errors,
    )
    require(
        systems.get("retired_model_reserved") is True
        and systems.get("hide_empty_retired_section") is True,
        "retired systems must be reserved but hidden while empty",
        errors,
    )

    lab = doc.get("lab", {})
    require(
        lab.get("landing_mode") == "directory-with-flagships",
        "Lab must use a directory-with-flagships landing mode",
        errors,
    )
    require(
        lab.get("ramone_first_major_experience") is True,
        "Ramone must remain the first major Lab experience",
        errors,
    )
    featured = {
        item.get("name"): item.get("maturity")
        for item in lab.get("featured", [])
        if isinstance(item, dict)
    }
    require(
        featured.get("System SYMPHONY") == "Preview",
        "System SYMPHONY must remain Preview in the first migration",
        errors,
    )
    require(
        featured.get("System Map") == "Tool"
        and featured.get("Proof Chain") == "Tool",
        "Lab featured tool maturity is invalid",
        errors,
    )
    groups = lab.get("groups", {})
    require(
        groups.get("Experience") == ["Ramone", "System SYMPHONY", "Signal Garden"],
        "Lab Experience group is invalid",
        errors,
    )
    require(
        groups.get("Observe")
        == ["System Map", "Status", "Activity", "Deployment evidence", "DORA metrics"],
        "Lab Observe group is invalid",
        errors,
    )
    require(
        groups.get("Verify")
        == ["Proof Chain", "Estate Conformance", "Reliability Trials", "API Docs"],
        "Lab Verify group is invalid",
        errors,
    )
    require(
        groups.get("Explore") == ["Shape Detector"],
        "Lab Explore group is invalid",
        errors,
    )
    require(
        lab.get("shape_detector_maturity") == "Experiment",
        "Shape Detector must remain an Experiment",
        errors,
    )
    require(
        lab.get("system_map_dedicated_route")
        == "https://atlas-systems.uk/lab/system-map/",
        "Lab System Map route is invalid",
        errors,
    )
    require(
        lab.get("move_dense_views_behind_cards_or_dedicated_routes") is True,
        "dense Lab views must move behind cards or dedicated routes",
        errors,
    )
    require(
        lab.get("experiment_data_mode_required") is True,
        "experiments must identify live, replayed, or simulated data",
        errors,
    )

    hierarchy = doc.get("page_hierarchy", [])
    require(
        hierarchy
        == [
            "global-header",
            "product-or-section-identity",
            "eyebrow-identifier-or-route-type",
            "page-title",
            "concise-purpose",
            "primary-state-or-action",
            "main-content",
            "supporting-evidence-and-metadata",
            "purpose-specific-footer-and-estate-escape",
        ],
        "default page hierarchy is invalid",
        errors,
    )

    components = doc.get("components", {})
    require(
        set(components.get("roles", [])) == REQUIRED_COMPONENT_ROLES,
        "component role set is incomplete",
        errors,
    )
    require(
        components.get("product_specific_components_remain_local") is True,
        "product-specific components must remain local",
        errors,
    )
    require(
        components.get("experimental_layout_freedom") is True,
        "experimental layout freedom must remain explicit",
        errors,
    )

    work = doc.get("work", {})
    require(work.get("disclosure") == "selective", "Work must use selective disclosure", errors)
    require(
        work.get("card_layers") == ["identity", "primary-evidence", "supporting-detail"],
        "Work card layers are invalid",
        errors,
    )
    require(
        work.get("permanent_project_identifiers") is True,
        "Work project identifiers must remain permanent",
        errors,
    )
    require(
        work.get("display_order_independent_from_identifier") is True
        and work.get("display_order_independent_from_publication_order") is True,
        "Work display order must be independent from identifiers and publication",
        errors,
    )
    require(
        work.get("sections")
        == ["Featured work", "All projects", "In development", "Experiments", "Retired work"],
        "Work sections are invalid",
        errors,
    )
    require(
        work.get("technology_pill_limit") == 6,
        "Work technology pill limit must be six",
        errors,
    )
    require(
        work.get("stable_anchors_required") is True,
        "Work stable anchors must be required",
        errors,
    )
    require(
        set(work.get("anchor_safeguards", []))
        == {"unique-ids", "scroll-margin-top", "automated-anchor-tests"},
        "Work anchor safeguards are incomplete",
        errors,
    )

    writing = doc.get("writing", {})
    require(
        writing.get("sections") == ["Featured", "Series", "All writing"],
        "Writing sections are invalid",
        errors,
    )
    require(
        writing.get("scheduler_owns_order_and_upcoming_visibility") is True,
        "scheduler must own Writing order and upcoming visibility",
        errors,
    )
    require(
        writing.get("only_next_or_next_series_visible") is True,
        "only the next article or next series may be visible",
        errors,
    )
    require(
        writing.get("scheduled_date_precision") == "month",
        "scheduled Writing dates must use month precision",
        errors,
    )
    require(
        writing.get("completed_series_uses_group_card") is True,
        "completed Writing series must use a group card",
        errors,
    )
    require(
        writing.get("secondary_tags_remain_generator_owned") is True,
        "secondary tags must remain generator-owned",
        errors,
    )
    archive = writing.get("archive_threshold_published_articles", {})
    require(
        archive == {"minimum": 15, "maximum": 20},
        "Writing archive threshold must remain 15 to 20 articles",
        errors,
    )
    historical = writing.get("historical_visual_migration", {})
    require(
        historical.get("canonical_source")
        == "regenerate-through-generator-and-scheduler",
        "canonical historical articles must use generator and scheduler",
        errors,
    )
    require(
        historical.get("missing_canonical_source")
        == "bounded-scheduler-shell-refresh-only",
        "source-less historical articles must use bounded scheduler refresh",
        errors,
    )
    require(
        historical.get("article_prose_rewrite_forbidden") is True,
        "historical visual migration must not rewrite article prose",
        errors,
    )

    about = doc.get("about", {})
    require(
        about.get("identity_order")
        == [
            "Systems Engineer",
            "Software and AI Engineer",
            "Audio Systems Specialist",
            "Game Developer",
        ],
        "About identity order is invalid",
        errors,
    )
    require(
        about.get("employer_name_public") is False
        and about.get("heritage_public") is False,
        "About must not publish employer name or heritage",
        errors,
    )
    require(
        about.get("saltire_scholarship_public") is True,
        "About must retain the Saltire Scholarship",
        errors,
    )
    require(
        about.get("contacts") == ["email", "GitHub", "LinkedIn"],
        "About contact methods are invalid",
        errors,
    )
    require(
        about.get("visual") == "photograph-plus-lightly-animated-topology",
        "About visual direction is invalid",
        errors,
    )
    require(
        about.get("reduced_motion_fallback_required") is True,
        "About topology must provide a reduced-motion fallback",
        errors,
    )

    visual = doc.get("visual", {})
    require(
        visual.get("density") == "spacious-editorial",
        "visual density must be spacious-editorial",
        errors,
    )
    require(
        visual.get("spacing_scale_px") == [4, 8, 12, 16, 24, 32, 48, 64, 96],
        "spacing scale is invalid",
        errors,
    )
    require(
        visual.get("control_height_px")
        == {"compact": 32, "standard": 40, "touch_target_minimum": 44},
        "control height scale is invalid",
        errors,
    )
    require(
        visual.get("card_padding_px")
        == {"compact": 16, "standard": 24, "editorial": 32},
        "card padding scale is invalid",
        errors,
    )
    require(
        visual.get("radius_px") == {"minimum": 4, "maximum": 8},
        "radius range is invalid",
        errors,
    )
    require(
        visual.get("heavy_glassmorphism_forbidden") is True,
        "heavy glassmorphism must remain forbidden",
        errors,
    )
    require(
        visual.get("imagery", {}).get("diagrams_encouraged") is True
        and visual.get("imagery", {}).get("information_first") is True,
        "visual imagery must remain diagram-led and information-first",
        errors,
    )

    distribution = doc.get("distribution", {})
    require(
        distribution.get("governance_owner") == "AtlasReaper311/atlas-infra",
        "distribution governance owner is invalid",
        errors,
    )
    require(
        distribution.get("implementation_owner") == "AtlasReaper311/atlas-interface-kit",
        "distribution implementation owner is invalid",
        errors,
    )
    require(
        distribution.get("implementation_owner_state")
        in {"approved-not-created", "active"},
        "distribution implementation owner state is invalid",
        errors,
    )
    require(
        distribution.get("runtime_assets") == "repository-local",
        "interface assets must remain repository-local",
        errors,
    )
    require(
        distribution.get("remote_runtime_dependency_forbidden") is True,
        "remote runtime interface dependencies must remain forbidden",
        errors,
    )
    require(
        distribution.get("update_delivery") == "automated-pull-requests",
        "interface updates must be delivered by automated pull requests",
        errors,
    )
    require(
        distribution.get("visual_merge_approval") == "manual",
        "visual updates must require manual merge approval",
        errors,
    )
    immutable = set(distribution.get("overrides", {}).get("immutable", []))
    require(
        {
            "focus-visibility",
            "semantic-state-colours",
            "minimum-text-contrast",
            "minimum-touch-target",
            "spacing-scale-values",
            "base-breakpoints",
            "global-header-contract",
            "z-index-layer-meanings",
            "reduced-motion-behaviour",
        }.issubset(immutable),
        "immutable token set is incomplete",
        errors,
    )

    evidence = doc.get("evidence", {})
    require(
        evidence.get("browsers") == ["Firefox", "Chrome"],
        "evidence browsers must be Firefox and Chrome",
        errors,
    )
    require(
        evidence.get("desktop_primary") is True,
        "desktop must remain the primary portfolio experience",
        errors,
    )
    require(
        evidence.get("mobile_required_after_desktop") is True,
        "mobile support must remain required",
        errors,
    )
    require(
        tuple(evidence.get("viewports_px", [])) == REQUIRED_VIEWPORTS,
        "evidence viewport matrix is invalid",
        errors,
    )
    require(
        evidence.get("all_changed_routes_require_full_screenshots") is True,
        "changed routes must produce full screenshots",
        errors,
    )
    require(
        evidence.get("all_routes_require_semantic_and_accessibility_checks") is True,
        "all routes must receive semantic and accessibility checks",
        errors,
    )
    require(
        evidence.get("manual_visual_approval_required") is True,
        "visual changes must require manual approval",
        errors,
    )
    require(
        evidence.get("serious_accessibility_failures_block_merge") is True,
        "serious accessibility failures must block merge",
        errors,
    )
    require(
        evidence.get("screenshots_use_deterministic_fixtures") is True
        and evidence.get("live_data_contract_tests_are_separate") is True,
        "visual fixtures and live-data contract tests must remain separate",
        errors,
    )

    editorial = doc.get("editorial", {})
    require(
        editorial.get("substantive_portfolio_claims_require_owner_approval") is True,
        "substantive portfolio claims must require owner approval",
        errors,
    )
    require(
        editorial.get("personal_narrative_requires_owner_approval") is True,
        "personal narrative must require owner approval",
        errors,
    )
    require(
        editorial.get("summary_shortening_requires_owner_approval") is True,
        "summary shortening must require owner approval",
        errors,
    )

    protected = set(doc.get("protected_identity", []))
    require(
        {
            "ramone-startup-experience",
            "homepage-primary-hero-character",
            "work-galleries-and-audio-evidence",
            "writing-editorial-character",
            "lab-purpose-specific-instruments",
            "status-bounded-state-semantics",
            "api-docs-openapi-authority",
            "cv-document-gate",
            "system-symphony-audio-behaviour",
        }.issubset(protected),
        "protected product identity set is incomplete",
        errors,
    )

    return ValidationResult(tuple(errors))


def validate_surface_manifest(
    doc: dict[str, Any],
    root: Path,
) -> ValidationResult:
    errors: list[str] = []
    require(
        doc.get("schema_version") == SURFACE_SCHEMA,
        "surface manifest schema_version is invalid",
        errors,
    )
    repository = doc.get("repository")
    require(
        isinstance(repository, str) and repository.startswith("AtlasReaper311/"),
        "surface manifest repository is invalid",
        errors,
    )
    surfaces = doc.get("surfaces")
    require(
        isinstance(surfaces, list) and bool(surfaces),
        "surface manifest must contain surfaces",
        errors,
    )
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
        require(
            bool(parsed and parsed.scheme == "https" and parsed.netloc),
            f"{prefix}.url must be an HTTPS URL",
            errors,
        )
        if isinstance(url, str):
            urls.append(url)

        source = surface.get("source")
        require(
            isinstance(source, str) and bool(source),
            f"{prefix}.source is required",
            errors,
        )
        if isinstance(source, str):
            require(
                (root / source).exists(),
                f"{prefix}.source does not exist: {source}",
                errors,
            )

        kind = surface.get("kind")
        require(kind in ALLOWED_KINDS, f"{prefix}.kind is invalid", errors)
        indexing = surface.get("indexing")
        require(indexing in ALLOWED_INDEXING, f"{prefix}.indexing is invalid", errors)
        require(
            surface.get("global_header") is True,
            f"{prefix} must declare the global header",
            errors,
        )
        require(
            surface.get("search") is True,
            f"{prefix} must declare estate search",
            errors,
        )
        require(
            surface.get("status_indicator") in ALLOWED_STATUS,
            f"{prefix}.status_indicator is invalid",
            errors,
        )
        if kind == "homepage":
            require(
                surface.get("status_indicator") == "homepage-owned",
                f"{prefix} homepage must own its status treatment",
                errors,
            )
        else:
            require(
                surface.get("status_indicator") == "aggregate-link",
                f"{prefix} non-home surface must use aggregate-link",
                errors,
            )
        if kind == "cv":
            require(
                indexing == "noindex, follow",
                f"{prefix} CV indexing must be noindex, follow",
                errors,
            )
        if kind == "error":
            require(
                indexing == "noindex, nofollow",
                f"{prefix} error indexing must be noindex, nofollow",
                errors,
            )
        if kind == "lab-home":
            require(
                surface.get("contextual_navigation") is True,
                f"{prefix} Lab home must declare contextual navigation",
                errors,
            )

        require(
            REQUIRED_ICON_FILES.issubset(set(surface.get("icons", []))),
            f"{prefix} icon declarations are incomplete",
            errors,
        )
        require(
            REQUIRED_METADATA.issubset(set(surface.get("metadata", []))),
            f"{prefix} metadata declarations are incomplete",
            errors,
        )
        require(
            surface.get("link_policy")
            == "atlas-owned-same-tab-external-safe-new-tab",
            f"{prefix} link policy is invalid",
            errors,
        )
        require(
            isinstance(surface.get("footer"), str) and bool(surface.get("footer")),
            f"{prefix}.footer is required",
            errors,
        )

    require(
        len(urls) == len(set(urls)),
        "surface URLs must be unique",
        errors,
    )
    return ValidationResult(tuple(errors))


def validate(root: Path, manifest: Path | None) -> ValidationResult:
    errors: list[str] = []
    try:
        contract = load_json(root / "policy/public-interface-contract.json")
        system = load_json(root / "policy/public-interface-system-v2.json")
        domains = load_json(root / "policy/atlas-owned-domains.json")
    except ValueError as exc:
        return ValidationResult((str(exc),))

    errors.extend(validate_contract(contract).errors)
    errors.extend(validate_system(system).errors)
    errors.extend(validate_domains(domains).errors)

    if manifest is not None:
        try:
            surface_doc = load_json(manifest)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            manifest_root = (
                manifest.parent.parent
                if manifest.parent.name == ".atlas"
                else root
            )
            errors.extend(
                validate_surface_manifest(surface_doc, manifest_root).errors
            )

    return ValidationResult(tuple(errors))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="atlas-infra repository root",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="optional repository .atlas/public-interface.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optional JSON report output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = validate(
        args.root.resolve(),
        args.manifest.resolve() if args.manifest else None,
    )
    report = {"ok": result.ok, "errors": list(result.errors)}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
    if not result.ok:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Public interface authority validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
