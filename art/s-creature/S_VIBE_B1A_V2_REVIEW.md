# EvoWild Run — S Vibe Gate B1a-v2 Review

Status: REVISE
Lane: exp/s-creature-vibe-modeling
Candidate: output/S-vibe-b1a-v2.blend
Source baseline: output/S-vibe-b0-v025.blend

## Review basis

Compared the actual five-view renders for:
- B0-v025
- B1a-v1
- B1a-v2

Views:
- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Comparison sheet:
- output/review/vibe-b1a-v2/B1a-v2-three-version-five-view-comparison.png

Repository S references checked:
- references/00_full_reference.png
- references/01_s_body_primary.png
- references/02_s_silhouette.png
- relevant repository S reference crops already used by the experimental lane

The separately referenced **"Modeling Image v1.0" is not present in the repository and was not independently inspected in this review. Do not claim it was reviewed.**

## Hard-scope validation

PASS.

B1a-v2 validation:
- method: boundary-tapered Taubin-style local relax
- lambda: 0.32
- mu: -0.33
- cycles: 4
- changed vertices: 914
- max displacement: 0.005832236968779116
- mean displacement: 0.000415489497275144
- fixed geometry unchanged: true
- preserved crest/toes unchanged: true
- topology unchanged: true
- render fixed geometry unchanged: true

The candidate is technically safe under the locked B1a scope.

## Visual result

B1a-v2 improves the shoulder/chest surface only slightly over B0-v025 and B1a-v1.

The remaining visible problem is still:
- unevenness / bumpiness around the shoulder root
- unevenness along the lateral chest surface
- FRONT34 still does not read as a sufficiently clean shoulder-to-chest transition

The stronger four-cycle relax produces a larger measurable displacement than B1a-v1, but the visual improvement is still insufficient.

## Decision

**REVISE**

Do not mark B1a-v2 as KEEP.

B1b remains blocked.

The main lane `feat/s-creature-model` remains unchanged.

## B1a-v3 — next single hypothesis

Source:
- **output/S-vibe-b0-v025.blend**

Reason:
- B1a-v2 passed safety validation but did not achieve enough visual cleanup.
- Re-start from B0-v025 to avoid accumulating local relax deformation from v1/v2.

Target:
- shoulder-root and lateral-chest bumpiness
- same locked B1a Y/Z region only

Keep fixed:
- every body vertex outside the B1a region
- crest
- all toes
- topology
- vertex count
- all other morphology

Exact edit:
- keep the same lambda / mu parameters and the same boundary taper
- change only local relax cycles from **4 to 8**

Expected visual change:
- reduce the fine unevenness visible around the shoulder root and lateral chest
- preserve shoulder mass and chest silhouette
- avoid broad silhouette drift

Hard limit:
- if maximum displacement exceeds **0.010**, fail and stop

Stop condition:
- render SIDE / FRONT / FRONT34 / REAR34 / BACK
- run hard-scope validation
- stop for actual-image review
- do not start B1b automatically
