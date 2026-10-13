# Chroma retention

The existing Chroma volumes are rollback assets, not part of the steady-state
Qdrant Compose project. They must remain untouched through the acceptance
window. Retention ends only after a separate owner decision records:

- the exact Qdrant and application commits in production;
- verified backup hashes and a successful restore drill;
- the acceptance-window end time;
- a rollback decision and decommission owner;
- confirmation that no application configuration still names Chroma.

No source change in this directory authorises deletion, compaction, or rewrite
of Chroma data.
