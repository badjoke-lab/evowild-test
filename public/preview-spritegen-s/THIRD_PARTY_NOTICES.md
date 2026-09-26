# sprite-gen evaluation lane — third-party note

This EvoWild Run proof-of-concept evaluates the workflow described by:

- Project: `aldegad/sprite-gen`
- License: Apache-2.0
- Pinned upstream commit for this evaluation: `fbd1a08d47e39c673c73eb494cfde8435b3b13b6`
- Upstream release metadata at that commit: `2.11.0`

No sprite-gen source code is copied into this directory.

The browser lane first produces a deterministic S-only side-view reference loop from EvoWild's current canonical S runtime asset. That reference is the QA baseline for the subsequent external sprite-gen motion pass; it prevents a generated loop from being accepted merely because it is animated.

The external pass remains intentionally isolated from P / E / A.
