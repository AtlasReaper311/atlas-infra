# Public interface programme Phase 6 footer authority

Status: Phases 6A through 6D Writing rollout are complete. Phase 6 remains open for authority reconciliation, independent consumer adoption, browser and accessibility evidence, and final closeout.

Opened: 29 July 2026.

## Purpose

Phase 6 defines the shared structural contract for purpose-specific Atlas Systems footers without making every product, tool, or article footer identical.

ADR-0008 already requires a purpose-specific footer and an estate escape. The base policies preserve local product identity, repository-local assets, independent deployment, shared focus behaviour, and same-tab navigation across Atlas-owned HTML surfaces. This phase converts that accepted direction into an executable slot and variant contract.

ADR-0009 records one bounded exception for classic Writing article footers. It does not weaken the normal estate, product, tool, or editorial variants.

## Phase 6A authority closeout

Phase 6A was reviewed through `AtlasReaper311/atlas-infra` PR #87 at exact head `ba611253d3806e21feb9c15b6607ddc49a2178aa` and squash-merged into `main` as `8d050790fbf08eb1ae41e2a9b47c1b2fa70d2c1` on 29 July 2026.

The exact-head pull-request checks passed:

- Public interface contract;
- Contract registry CI;
- Pull request impact;
- CodeQL;
- OpenSSF Scorecard.

The Dependabot review policy was skipped as intended for a non-Dependabot pull request. No review threads remained open.

## Phase 6B implementation closeout

`AtlasReaper311/atlas-interface-kit` PR #13 implemented the accepted footer authority as `v0.4.0`.

- Reviewed head: `519124ab11d8217ca0516dd475271270426bc337`.
- Squash merge commit: `c38b5b3edd631999dfad838c4fb70e505a9860cf`.
- Merge date: 29 July 2026.
- Exact-head CI, CodeQL, and OpenSSF Scorecard checks passed.
- No review threads remained open.

The implementation added estate, product, tool, and editorial variants; identity, context, evidence, sequence, and estate-escape slots; responsive layout and focus foundations; machine-readable footer semantics; deterministic release coverage; and explicit scheduler and consumer ownership boundaries.

## Phase 6C immutable release closeout

The immutable `atlas-interface-kit v0.4.0` release was published and independently verified on 29 July 2026.

### Source and tag

- Source commit: `c38b5b3edd631999dfad838c4fb70e505a9860cf`.
- Annotated tag: `v0.4.0`.
- The tag resolves exactly to the source commit with zero commit difference.

### Release workflow

- Workflow: `Release`.
- Run ID: `30458258099`.
- Trigger: tag push.
- Head branch: `v0.4.0`.
- Head SHA: `c38b5b3edd631999dfad838c4fb70e505a9860cf`.
- Conclusion: success.
- Run URL: `https://github.com/AtlasReaper311/atlas-interface-kit/actions/runs/30458258099`.

### Independent verification

A fresh local deterministic build was compared byte-for-byte with the workflow artifact and the subsequently published GitHub Release assets.

- Archive: `atlas-interface-kit-0.4.0.tar.gz`.
- Archive SHA-256: `6b72d8acb07230f0b25d4b78b5c5b081ab09a296f11ad3ac1b1f5cb493cac9b9`.
- Archive size: `102698` bytes.
- Release manifest: `atlas-interface-kit-0.4.0.release-manifest.json`.
- Manifest SHA-256: `86fcd399a451f99175cffc8e44abf4f404495f409fc1bfd751d95dfd1b86bbb3`.
- Manifest size: `3260` bytes.
- Verified release file count: `19`.
- `docs/FOOTER_EXTENSION.md` was present.

The published asset digests match the independent verification hashes exactly.

### Published release

- Name: `atlas-interface-kit v0.4.0`.
- Tag: `v0.4.0`.
- Published: `2026-07-29T13:55:22Z`.
- Draft: false.
- Prerelease: false.
- Release URL: `https://github.com/AtlasReaper311/atlas-interface-kit/releases/tag/v0.4.0`.

Phase 6C changed no consumer source, generated Writing output, scheduler state, runtime deployment, provider setting, or secret.

## Phase 6D Writing rollout evidence

The Writing pipeline rollout completed before final Phase 6 closeout inspection.

- `atlas-article-gen` PR #36 merged as `6f0a0a48fd6e608d2f81f5e021c130de20aecb05`.
- Generated draft refresh commit `a492c599cdb7055ca4e8aebd8dd5a4d74ec30d82` retained the classic article footer shell.
- `atlas-scheduler` PR #41 merged as `1abb026aa166235a7182000c20e85406e62ab028`.
- W-05 scheduler request `b723f8ddfb30ca39e307c43b4ca078c07186cae4` produced site commit `df72b956b03f6688667be7e7d85a4b9f1a33c6f1`.
- W-06 scheduler request `5c5cdd798cc39cdace6824f5aa8bd98484260bca` produced site commit `225092aaa07909445eb2e796aee74333cfe56696`.
- W-07 scheduler request `a5cb581d03d0cc484a82b5f6bccefd12c25a683a` produced site commit `9cc324591e5ad6346762ed590fba9d5b7c8f45a1`.
- The W-05, W-06, and W-07 receipts record `exact_deployment_verified: true`.

The owner-approved Writing structure for W-01 through W-07 is:

```html
<div class="article-footer">
  <!-- scheduler-owned previous and next links, or Latest article -->
</div>
```

It intentionally excludes an editorial identity row, Writing-index row, estate-escape row, `.atlas-footer` wrapper, and `.atlas-footer__sequence` wrapper.

## Accepted intentional difference

ADR-0009 accepts `classic_writing_articles` as a non-transferable intentional difference.

The difference:

- permanently covers W-01 through W-07;
- covers current generator output until the Phase 10 editorial surface review;
- applies only to the `atlas-article-gen`, `atlas-scheduler`, and `atlas-systems` publication path;
- preserves generator ownership of the shell and single scheduler placeholder;
- preserves scheduler ownership of sequence and publication;
- creates no new `atlas-interface-kit` variant or release;
- cannot be claimed by estate, product, tool, Lab, index, error, or other editorial surfaces.

The normal four variants and five slots remain unchanged.

## Evidence inspected

Part 0 inspected current authority and current footer implementations in:

- `AtlasReaper311/atlas-systems`;
- `AtlasReaper311/status`;
- `AtlasReaper311/atlas-api-public`;
- `AtlasReaper311/ramone-edge`;
- `AtlasReaper311/atlas-doc-viewer`;
- `AtlasReaper311/atlas-article-gen`;
- `AtlasReaper311/atlas-scheduler`;
- `AtlasReaper311/atlas-interface-kit`.

The inspection found four real footer families:

1. estate footers on the primary portfolio surface;
2. product footers on Status, Public API Docs, Ramone, and CV;
3. tool footers on Lab tools and experiments;
4. editorial footers whose previous and next links are computed by the publishing pipeline.

## Accepted contract

The normal footer role remains `.atlas-footer` and uses a semantic `footer` element.

A normal page has one primary footer. When a page has more than one footer landmark, each requires an accessible name. Empty footers and empty rendered slots are forbidden.

The ADR-0009 classic Writing profile is the only accepted exception to the normal component shape.

### Slots

| Slot | Requirement | Ownership |
| --- | --- | --- |
| Identity | Required | Consumer-owned name for the estate, product, tool, section, or editorial surface |
| Context | Optional except on tool footers | Consumer-owned local destinations that do not duplicate the complete global navigation |
| Evidence | Optional | Consumer-owned links to relevant source, status, documentation, or operational evidence |
| Sequence | Required only on editorial footers | Consumer- or publisher-owned ordered navigation; article chaining remains scheduler-owned |
| Estate escape | Required | Consumer-owned route from the local surface into the wider Atlas Systems estate |

### Variants

| Variant | Required slots | Optional slots | Forbidden slots |
| --- | --- | --- | --- |
| Estate | identity, estate escape | context, evidence | sequence |
| Product | identity, estate escape | context, evidence | sequence |
| Tool | identity, context, estate escape | evidence | sequence |
| Editorial | identity, sequence, estate escape | context, evidence | none |

Variant selection describes information architecture. It does not permit local consumers to override focus visibility, minimum touch targets, base breakpoints, reduced-motion behaviour, semantic state colours, or link policy.

## Shared behaviour

Normal footer implementations must:

- use purpose-specific labels;
- avoid reproducing the complete global navigation;
- keep Atlas-owned HTML destinations in the same tab;
- open external destinations in a new tab with `rel="noopener noreferrer"`;
- preserve visible focus;
- provide 44-pixel minimum interactive targets;
- wrap without horizontal clipping;
- retain clearance above fixed mobile bottom navigation;
- preserve reduced-motion behaviour;
- keep runtime assets repository-local;
- introduce no shared runtime JavaScript or remote presentation dependency.

## Ownership

### `atlas-infra`

Owns policy, schema, validation, release approval, and accepted architecture traceability.

### `atlas-interface-kit`

Owns selectors, layout foundations, responsive behaviour, focus foundations, and immutable repository-local distribution for normal footer variants.

It must not own consumer wording, consumer destinations, publication sequencing, runtime data, or the classic Writing exception.

### `atlas-article-gen`

Owns the article shell, the single scheduler footer placeholder, and generator tests.

It does not own due-date selection, published previous and next chaining, or production writes.

### `atlas-scheduler`

Owns published article footer chaining, previous and next labels, series sequencing, and the only write path into `atlas-systems`.

A dry run and any production execution remain separately approval-gated.

### Consumers

Each consumer owns its footer content, variant selection, local links, rendering integration, tests, preview, and rollback.

Every adoption requires a separate pull request, visual review, merge approval, and rollout approval.

## Distribution

The accepted implementation release remains `atlas-interface-kit v0.4.0`.

Consumers may adopt only from that immutable release and must verify copied repository-local files against its published manifest.

ADR-0009 does not change or republish that release.

## Validation

Repository-native validation for this authority record remains:

```bash
python3 -m py_compile \
  scripts/validate_public_interface.py \
  scripts/validate_public_interface_foundation_extension.py \
  scripts/validate_public_interface_footer_extension.py
python3 scripts/validate_public_interface.py --root .
python3 scripts/validate_public_interface_foundation_extension.py --root .
python3 scripts/validate_public_interface_footer_extension.py --root .
python3 -m unittest \
  scripts.tests.test_validate_public_interface \
  scripts.tests.test_validate_public_interface_foundation_extension \
  scripts.tests.test_validate_public_interface_footer_extension \
  -v
python3 scripts/adr_trace.py check --root .
git diff --check
```

Pull-request checks remain authoritative for the exact branch bytes.

## Next gate

Merge the focused `atlas-infra` authority reconciliation pull request before downstream repositories treat ADR-0009 as accepted authority.

After that merge:

1. update `atlas-article-gen` documentation and tests without regenerating article output;
2. update `atlas-scheduler` documentation, publication validation, and tests without running the scheduler;
3. prepare separate consumer footer draft pull requests using immutable `atlas-interface-kit v0.4.0` assets;
4. keep `/lab/console/` deferred to Phase 11;
5. collect browser and accessibility evidence;
6. seek separate merge and rollout approvals;
7. close Phase 6 through a final `atlas-infra` evidence pull request.

No generated article output may be hand-edited. No workflow dispatch, preview deployment, production deployment, scheduler execution, publication, provider write, or secret change is authorized by this record.
