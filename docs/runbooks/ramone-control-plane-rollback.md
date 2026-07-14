# Ramone control-plane rollback

Use this runbook only for the additive Phase 9 Atlas surfaces.

1. Disable the Atlas external tool-server assignment in OpenWebUI.
2. If necessary, remove only the Atlas external-tool connection. Do not edit
   another tool group, Ramone identity, prompt, model, or memory attachment.
3. Disable or remove only the Atlas Home Assistant sensor package and
   dashboard registration. Keep the existing estate package and all device
   controls untouched.
4. Run Home Assistant's configuration check before any separately approved
   reload or restart.
5. Stop the bounded read-model producer if one was later enabled. Do not delete
   source evidence or mutate a provider.
6. Revert the focused `atlas-api-public`, `ramone-memory`, and `atlas-infra`
   pull requests independently when repository rollback is required.

Rollback is complete only when the prior Ramone identity, prompt, model,
memory, Home Assistant control/lights, SPECULAR, phone/watch, wake word,
Wyoming STT/TTS, response media player, and spoken behavior remain available
through their original paths.
