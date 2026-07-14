# Cost guard: policy owner missing

## Trigger

An enabled service/quota policy entry has no non-empty owner.

## Safe response

1. Identify the owning repository and service from the canonical estate records.
2. Ask the estate owner to confirm the accountable person/team.
3. Add the owner through a focused `atlas-infra` policy pull request.
4. Re-run policy validation and the affected fixture.

Do not guess ownership or route the finding automatically. Until confirmed, the
meter remains `unknown` and any action remains advisory-only.
