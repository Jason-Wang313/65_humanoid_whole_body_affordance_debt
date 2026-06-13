# ICLR Main Gate

Paper: 65 humanoid_whole_body_affordance_debt

Existing v2 decision: KILL_ARCHIVE

Gate verdict: KILL_ARCHIVE

Evidence digest: pending-v4-real-mujoco

Resolved blockers:
- Synthetic-only evidence replaced by real MuJoCo articulated whole-body rollouts.
- Implemented affordance-debt mechanism.
- Implemented random, arm-only, greedy, comfort, robust-balance, and oracle baselines.
- Added multi-seed metrics, ablations, pairwise tests, and figures.

Fatal remaining blockers:
- Greedy/comfort/robust baselines match the proposed method.
- No-debt and reduced-debt ablations match the full mechanism.
- No hardware or public humanoid benchmark validation.
- Manual exhaustive related-work synthesis remains incomplete.

The only honest main-conference-safe decision is to archive rather than overclaim.
