# Paper 65 ICLR-Main Execution Plan

Date: 2026-06-15

Paper: `65_humanoid_whole_body_affordance_debt`

Goal: verify whether the current real MuJoCo articulated-body evidence justifies keeping the paper at `KILL_ARCHIVE`, or whether any evidence supports revival to `STRONG_REVISE` or ICLR-main readiness.

## Execution Gates

1. Reproducibility gate:
   - Compile `src/run_experiment.py`.
   - Confirm main, seed, paired, ablation, stress, and negative-case CSV outputs exist.
   - Confirm all CSV outputs are non-empty and finite.
   - Rebuild the PDF from `paper/main.tex` with BibTeX.

2. Evidence gate:
   - Confirm the benchmark uses real MuJoCo articulated-body rollouts rather than synthetic tables.
   - Confirm seven stress splits, multiple seeds, paired comparisons, confidence intervals, and combined-shift ablations.
   - Confirm baselines include random posture, arm-only reach, greedy reach MPC, comfort-regularized MPC, robust balance MPC, and oracle two-step MPC.

3. Negative-claim gate:
   - Compare affordance-debt MPC against greedy reach MPC.
   - Compare affordance-debt MPC against comfort-regularized MPC.
   - Compare affordance-debt MPC against robust balance MPC.
   - Check whether no-future-debt, no-balance-margin, no-recovery-cost, no-comfort, and small-sample ablations degrade performance.
   - Fix stale docs that still describe synthetic-only evidence as the current reason for archive.

4. Artifact gate:
   - Rebuild `paper/main.pdf`.
   - Copy only `C:/Users/wangz/Downloads/65.pdf`.
   - Confirm `C:/Users/wangz/Desktop/65.pdf` is absent.
   - Confirm the GitHub repository is public and pushed.

## Decision Rule

Upgrade only if affordance-debt MPC clearly beats greedy, comfort, and robust non-oracle baselines and ablations show future debt is necessary. If the current ties remain, keep the terminal decision as `KILL_ARCHIVE` and document that the mechanism is falsified by real evidence.
