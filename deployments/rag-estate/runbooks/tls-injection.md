# TLS injection boundary

The protected source is:

```text
U:\runtime-secrets\rag-estate\tls\ca.pem
U:\runtime-secrets\rag-estate\tls\cert.pem
U:\runtime-secrets\rag-estate\tls\key.pem
```

The steady-state Compose project does not bind this Windows directory into the
non-root containers. That path was proven unsuitable for the Qdrant private-key
read check during disposable rehearsal. The approved installation step must:

1. verify the source filenames, hashes, certificate subject/SAN, and validity;
2. create or reuse only the named Docker volume `rag-estate_qdrant-tls`;
3. copy the three files without printing their contents;
4. set ownership/read permissions so Qdrant UID `65532` can read them but no
   container process can write them;
5. verify the volume contains no other files;
6. run Compose config validation and a private TLS/auth health check.

This runbook is preparation only. It does not create credentials, rotate
certificates, populate the production volume, or start services.
