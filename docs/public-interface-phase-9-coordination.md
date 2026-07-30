# Public interface programme Phase 9 closeout

Status: complete.

Recorded: 30 July 2026.

## Outcome

Phase 9 replaced the repeated section cadence on the focused Systems detail routes with one explicit analytical sequence:

1. Observability answers what is happening now.
2. Reliability answers whether the measured behaviour supports the reliability claims.
3. Evidence answers what records prove the public claims.

The three routes now provide semantic Systems breadcrumbs, route-specific evidence boundaries, a shared three-question sequence, stronger primary-versus-supporting hierarchy, clearer freshness and provenance presentation, and responsive narrow-layout ordering.

## Coordination receipt

The accepted scope and protected boundaries were recorded through `AtlasReaper311/atlas-infra` pull request #96.

- Reviewed head: `7e7cd8d31b71c85d88bc2a098259150713fa60f0`.
- Merge commit: `c43148d8fc7bbaecf79753f612ea44593459dbe8`.
- Changed paths: `docs/public-interface-phase-9-coordination.md` and `docs/work-allocation.md`.

The coordination merge changed documentation only. It did not deploy a consumer, publish content, dispatch a workflow, modify a provider, or change a secret.

## Source implementation receipt

The implementation was reviewed through `AtlasReaper311/atlas-systems` pull request #183.

- Branch: `refactor/systems-detail-surfaces`.
- Reviewed head: `46eadf4f2322b87f6b35cf3d6891d646a5201470`.
- Merge commit: `4dd5827b922832efacba4e20146de8dc2e95a1e7`.
- Changed paths: six.

The six-path source boundary was:

- `systems/reliability/index.html`;
- `systems/observability/index.html`;
- `systems/evidence/index.html`;
- `static/css/systems-detail-surfaces.css`;
- `js/tests/phase-9-systems-detail-surfaces.test.mjs`;
- `docs/PHASE-9-SYSTEMS-DETAIL-SURFACES.md`.

No route JavaScript, endpoint, request method, field allowlist, response parser, workflow, deployment configuration, provider setting, binding, secret, generated Writing output, publication path, or System Symphony runtime changed.

Stale pull request `atlas-systems#179` was not reused or merged.

## Exact-head validation and preview evidence

The source head passed the repository-native HTML, JavaScript, Lab, System Symphony, sitemap, static-performance, Pages-output, social-preview, JSON, whitespace, offline-link, public-interface conformance, CodeQL, and OpenSSF gates.

The approved isolated preview ran as GitHub Actions run `30580400479` against exact head `46eadf4f2322b87f6b35cf3d6891d646a5201470`.

All preview jobs succeeded:

- Validate interface preview candidate;
- Require approved browser evidence;
- Publish non-production interface preview;
- Capture deterministic interface evidence.

The deterministic evidence job completed the route-derived browser and viewport matrix, Batch H product assertions, System Map AtlasField pixel checks, directory-header AtlasField checks, and visual and accessibility uploads.

Preview artifacts:

- validation artifact `8774372662`, digest `sha256:dff57243f7cd5bfe07020a61d28b4c204fc92278a9e6ad5a1a6725be77246611`;
- route-derived evidence artifact `8774909887`, digest `sha256:51bfa086ec72555365c1d8a185c52f13cdeadd74543d9b0d72f6fc3a05eee3a1`;
- Batch H evidence artifact `8774910647`, digest `sha256:47394fefcbd2a00d3c0ecb8f1565775c36bbad940251da29d17d7a162a271886`.

The isolated preview was `https://interface-pr-183.atlas-systems-44t.pages.dev` and remained separate from production until merge approval.

## Production deployment and live verification

Merging source pull request #183 triggered repository-owned production run `30582815398` on `atlas-systems/main` at exact merge commit `4dd5827b922832efacba4e20146de8dc2e95a1e7`.

Every production job completed successfully:

- Verify Pages output contract, job `91007031570`;
- deploy / Validate HTML and links, job `91007077355`;
- deploy / Deploy to Cloudflare Pages, job `91007160368`;
- deploy / Report to Discord, job `91007246035`;
- Verify production custom domain, job `91007289765`;
- refresh-corpus / refresh, job `91008469397`.

The custom-domain job confirmed that `https://atlas-systems.uk` served build commit `4dd5827b922832efacba4e20146de8dc2e95a1e7`. It also confirmed the live Systems route marker and the governed Phase 6 footer assets.

The same job passed the production homepage AtlasField smoke and the live System Symphony Atlas APU, topology-map, and 32-bar loudness smoke against the exact deployment commit.

Production artifacts:

- homepage AtlasField smoke artifact `8775320803`, digest `sha256:6d7ad5aff8e8d55dd9e0d91878a88ae1f9764babd014e04f1292c86e01512162`;
- System Symphony smoke artifact `8775441001`, digest `sha256:27fa88beeead8babe4029bdaf9ab55eb86177784d17c5e00974981920cdfef55`.

The route-specific Observability, Reliability, and Evidence presentation was already exercised on the exact reviewed source head by the deterministic preview matrix. Production then proved that the merge commit containing those exact route bytes was served by the custom domain. No deployment result is inferred from merge state alone.

## Preserved boundaries

Phase 9 preserved:

- all existing endpoint URLs, methods, fetch timing, and response parsing;
- fixed field allowlists and `textContent` rendering;
- stale, malformed, unavailable, unmeasured, and insufficient-evidence semantics;
- script-owned dynamic identifiers;
- table semantics and dense-data overflow behaviour;
- current footer installation and tool variant;
- exact-route AtlasField compositions, seeds, host selector, pointer transparency, and reduced-motion behaviour;
- System Symphony audio and telemetry behaviour;
- Writing generation, scheduler sequencing, publication timing, and generated article ownership;
- provider configuration, bindings, repository settings, and secrets.

## Closeout decision

Phase 9 is complete.

The accepted six-path implementation is merged, the exact source head passed its deterministic preview and accessibility evidence gates, production run `30582815398` deployed the exact merge commit, the custom domain exposed that commit, and the repository-owned live smoke checks passed.

Phase 10 may begin only through a fresh Part 0 inspection of the current Writing pipeline and published reading surfaces. No Phase 10 source change, generator build, scheduler synchronization, publication, workflow dispatch, provider write, or secret change is authorised by this closeout.

## Rollback

A source rollback requires a reviewed revert in `atlas-systems`, the normal production deployment, exact-commit custom-domain verification, and representative live browser evidence. This documentation record can be reverted independently if any receipt is later shown to be inaccurate.
