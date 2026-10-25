# EvoWild Run / Codex — interrupted session and usage quota protocol
Status: REQUIRED for all 2.5D Codex sessions. Scope: work from the verified PR #131 child branch, never main.

## The failure mode
A per-hour/session token/tool quota can stop Codex *without any chance to finish the current response or push*. No instruction, timer, auto-save claim or CI workflow can guarantee protection against a sudden hard stop. The only durable checkpoint is material verified on `origin`.

## Rules that must be followed

**1. One bounded deliverable at a time.** No launch-and-forget mega-task. Examples: import 11 verified original PNGs; verify baseline; fix one race-history bug; test one complete player path; fix one mobile overlay defect. Avoid simultaneous unrelated feature work and avoid reworking all creature art.

**2. Mandatory frequent save.** After each meaningful edit/test cycle, or no later than **15 minutes of actual work**, whichever is sooner:
- Save source and tests in a sensible, compiling or honestly `WIP` commit on the **child branch**, then `git push -u origin HEAD`.
- Record the `git rev-parse HEAD`, `git status --short` and remote commit `git ls-remote origin refs/heads/<current-branch>`.
- Update **`docs/2p5d/HANDOFF_STATE.json`** on that same child branch. This includes actual status, current feature, completed substeps, unfinished substeps, test failures, evidence paths, last previously verified remote SHA, and **the next exact command**. Commit/push that checkpoint file too; verify remote SHA again.
- A checkpoint is not durable if remote inspection fails. Never report success of push unless verified. Keep uncommitted files rather than resetting/deleting them if the network fails.
- If binary assets exceed GitHub limits, stop and report the specific limit. Do not silently omit or substitute the user mock images.

**3. Advance estimate / near quota.** Codex may not have an accurate remaining quota meter. At *any* sign of tool rejection, resource budget pressure, repeated failures or long-running execution: **stop taking on new work immediately**. Try to commit/push current safe changes and update state. If that fails, report the exact last confirmed remote SHA and uncommitted files. Do not spend remaining calls on unrelated research.

**4. Resume without duplication.** On a new Codex session:
```bash
git fetch origin --prune
git branch -vv
git status --short
git log -5 --oneline
cat docs/2p5d/HANDOFF_STATE.json
```
Switch to the tracked child branch if already present; otherwise check out the origin child branch *without resetting user changes*. Verify HEAD and remote. If the checkpoint and Git remote disagree, inspect their commits/files and reconcile; **never reset --hard**, never assume prior pending files vanished, never repeat binary imports if hashes already pass. Then perform **only** `next_action` and unfinished steps. Update checkpoint and push again.

**5. Don't confuse checkpoints with release.** An isolated test passing does not approve visual quality. Keep main unchanged; child Draft PR only. Existing 2.5D 3/4 side-billboard visuals remain REVISE. Keep real screenshots, compile/test logs, and reference hash-verification results in tracked evidence or named Actions artifacts.

**6. Session ending message**, whether normal or hitting soft limits, must include:
- child branch / last actually verified origin SHA / Draft PR URL;
- exactly which changes are on origin vs local-only;
- successful/failed/not-run tests and run URLs;
- active blockers, reference mock state, quality gate (KEEP/REVISE);
- exact next commands from checkpoint.
Do not claim invisible background continuation or an automatic retry. The user can simply reopen Codex with the resume message below.

## Copy-ready resume prompt (short)
> EvoWild Run 2.5D: resume the previously started Codex child branch. First fetch origin and read AGENTS.md, docs/2p5d/CODEX_QUOTA_RECOVERY_PROTOCOL.md, docs/2p5d/HANDOFF_STATE.json, and git log/status. Verify the latest **remote-confirmed** SHA. Do **not** restart completed stages or regenerate mocks. Continue the first unfinished `next_action` in small independently testable units, committing and pushing after each, checking origin after pushes. Update and push HANDOFF_STATE.json before quota becomes uncertain. No main merge, no paid actions. Report PR, real evidence and remaining issues.
