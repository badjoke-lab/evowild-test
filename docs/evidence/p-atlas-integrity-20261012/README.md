# P 2.5D atlas chroma anomaly audit — provisional

Investigate visually apparent horizontal streaks, magenta/blue artifacts and contaminated transparency in `public/concept/p-run-sheet.webp`. The production sprite and `public/concept/P.webp` are **not modified**.

The browser decodes the actual RGBA spritesheet and counts highly noncanonical neon colors outside the intended cyan eye region. The generated overlay and per-phase statistics are **diagnostic**; they do not fully detect dim red/brown streaks and are not sufficient alone to label pixels for deletion. A candidate matte must be visually reviewed before any integration.

If anomaly mask is substantial, the earlier P 12-phase asset cannot be treated as finished artwork simply because loop overlap and test suites pass. Prior KEEP applies only to loop behavior. Any cleanup must preserve the original image and each pose's proper creature shape and silhouette.
