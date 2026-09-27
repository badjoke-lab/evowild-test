# Start here

This package is prepared to minimize model/context usage and to survive Astra/Work limits.

## In Work
1. Select **GPT-6 Astra** for the morphology-critical pass.
2. Give Work this folder/package.
3. Paste `WORK_START_PROMPT.txt`.
4. Let it work from `CHECKPOINT.md` without re-auditing old chat history.

If Astra becomes unavailable or hits its allowance, **stay in the same Work task** and switch the model picker to **Sol** (GPT-6 Sol, or GPT-5.6 Sol if that is the Sol option shown for the account), then paste `SOL_RESUME_PROMPT.txt`.

Read order for any agent:
1. `CHECKPOINT.md`
2. `ASTRA_TASK.md`
3. `references/01_s_body_primary.png`
4. `references/02_s_silhouette.png`
5. `WORK_EXECUTION_PLAN.md` only when a model/session handoff is needed

The package already contains S-specific reference crops, Blender scene/review scripts, checkpoint/resume files, and machine-readable handoff state.

Do not spend model context re-auditing this package unless a file fails to open.
