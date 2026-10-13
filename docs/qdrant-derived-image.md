# Qdrant derived image publication

This directory contains the reviewed, server-only Qdrant derivative used for
private disposable validation. The build inputs are source-controlled and all
base images are pinned by full digest.

The publication workflow:

- builds only linux/amd64;
- publishes only a full-source-commit tag under the approved private GHCR
  repository;
- emits BuildKit provenance and an SBOM attestation;
- attaches GitHub build provenance to the published digest;
- pulls the digest back into the CI runner before scanning it;
- records architecture, source labels, digest, SBOM, vulnerability, secret,
  and license evidence as an artifact.

The image is not a production approval. The final registry package visibility,
attestation verification, and the complete disposable RAG rehearsal must still
be checked from WSL before any production decision.

The image intentionally contains no application credentials, Qdrant API keys,
TLS keys, or live data. Runtime secrets remain outside this repository and are
injected only by the private deployment control plane.
