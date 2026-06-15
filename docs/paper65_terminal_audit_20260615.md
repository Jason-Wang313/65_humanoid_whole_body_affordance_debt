# Paper 65 Terminal Audit

Date: 2026-06-15

Paper: `65_humanoid_whole_body_affordance_debt`

Decision: `KILL_ARCHIVE`

ICLR-main ready: no

## Commands Executed

- `python -m py_compile src\run_experiment.py`
- CSV finite/schema audit over `results/affordance_debt_raw.csv`, `results/affordance_debt_metrics.csv`, `results/affordance_debt_pairwise.csv`, `results/affordance_debt_ablation.csv`, `results/affordance_debt_seed_metrics.csv`, `results/negative_cases.csv`, and compatibility CSVs.
- `pdflatex`, `bibtex`, `pdflatex`, `pdflatex` in `paper`
- `Copy-Item paper\main.pdf C:\Users\wangz\Downloads\65.pdf -Force`

## Verified Evidence

- Real MuJoCo articulated-body whole-body reaching benchmark is implemented in `src/run_experiment.py`.
- Main evidence contains 2,940 paired rows: 7 stress splits, 5 seeds, 12 episodes per seed/split/method, and 7 methods.
- Ablation evidence contains 420 rows on the combined-shift split.
- Baselines include random posture, arm-only reach, greedy reach MPC, comfort-regularized MPC, robust balance MPC, and oracle two-step MPC.
- The stale hostile-review response was updated to reflect that the current archive decision is based on real negative evidence, not synthetic-only evidence.
- The rebuilt PDF is `C:/Users/wangz/Downloads/65.pdf`.
- `C:/Users/wangz/Desktop/65.pdf` is absent.

## Fatal Results

The affordance-debt mechanism is falsified by the current evidence:

- Combined shift: affordance debt, greedy reach, and robust balance all reach `0.733 +/- 0.113` sequential success; energy differs by about `0.001`.
- High reach: affordance debt, greedy, comfort, robust, and oracle all reach `0.967 +/- 0.046`.
- Lateral reach: affordance debt, greedy, and robust all reach `0.400 +/- 0.125`.
- Nominal: affordance debt, greedy, comfort, and robust all reach `0.467 +/- 0.127`.
- Payload shift and weak actuation also show no sequential-success gap over greedy/robust baselines.
- Combined-shift ablations are fatal: `no_future_debt`, `no_balance_margin`, `no_recovery_cost`, `no_torque_comfort`, `small_future_sample`, and `current_target_only_greedy` all match the full method at `0.733 +/- 0.113` sequential success.

## Gate Decision

This paper satisfies the local evidence-package requirements for a real negative result: high-fidelity simulator evidence, articulated-body rollouts, paired baselines, ablations, stress tests, uncertainty, negative cases, rebuilt PDF, corrected hostile-review documentation, and public repository.

It does not satisfy `STRONG_REVISE` because the core future-affordance-debt term is not merely under-validated; it is unnecessary in the tested benchmark. The correct terminal state remains `KILL_ARCHIVE`.

Required revival work:

- invent a substantially different future-affordance mechanism that changes first-posture selection;
- prove gains over greedy, comfort, and robust balance baselines;
- show ablations where future debt is necessary;
- validate on hardware or a public humanoid benchmark;
- perform manual full-paper related-work synthesis.
