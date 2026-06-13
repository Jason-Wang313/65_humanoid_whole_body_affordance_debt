# Paper 65 Rebuild Plan: Humanoid Whole-Body Affordance Debt

Date: 2026-06-13

## Goal

Rebuild Paper 65 from a synthetic archive into a real ICLR-main-target empirical robotics submission, or terminate it honestly as `STRONG_REVISE` / `KILL_ARCHIVE` if the evidence does not support the claim.

Target claim:

> Current whole-body posture choices can create measurable future affordance debt: they may solve the immediate reach/manipulation target while reducing later reachability, balance margin, and recovery options. A planner that estimates and penalizes this debt should improve sequential humanoid manipulation under posture, friction, support, and payload shifts.

## Starting Audit

The current repository is not submission-ready:

- `src/run_experiment.py` is a synthetic probability-table generator.
- `paper/main.tex` is an archive memo.
- Existing docs mark the paper `KILL_ARCHIVE`.
- There is no high-fidelity simulator benchmark, implemented learned/fitted mechanism, real baselines, ablations, paper-specific plots, or manual related-work synthesis.

The rebuild must replace the evidence core, not edit the archive language.

## Non-Negotiable Evidence Bar

The paper may move toward submission only if it produces:

- Real MuJoCo articulated-body rollouts with contacts, joint torques, center-of-mass motion, and foot/support constraints.
- A concrete affordance-debt mechanism that estimates future reachability/balance loss from current posture.
- Sequential tasks where the first posture affects future targets.
- Strong implemented baselines, including greedy whole-body reach and robust recovery-aware planning.
- Multi-seed evaluation with confidence intervals and paired comparisons.
- Stress tests over support width, floor friction, payload, target height/lateral offset, actuation weakness, and perturbations.
- Ablations isolating debt, balance margin, future-target sampling, recovery simulation, and torque/comfort penalties.
- Paper-specific figures generated from real result CSVs.

If the custom MuJoCo evidence is unstable, too weak, or only beats trivial baselines, the paper must be `STRONG_REVISE` or `KILL_ARCHIVE`, not submission-ready.

## Benchmark Design

Use a lightweight MuJoCo humanoid-style whole-body reach benchmark:

- Articulated standing body with pelvis/torso, two feet in contact, and two arms.
- Candidate first postures choose torso lean, pelvis/hip stance, and left/right arm configuration to reach a first target.
- After the first posture settles, a second target is sampled. The same simulated body must recover or transition and reach the future target.
- Metrics include immediate target distance, final sequential success, center-of-mass support margin, foot contact loss, torso tilt, torque/effort, future reachability count, and energy.

The benchmark should remain CPU-light by using short MuJoCo rollouts and a finite candidate posture set rather than training a large neural policy.

## Method To Implement

Implement `affordance_debt_mpc`:

1. Generate candidate whole-body postures for the current target.
2. Simulate each candidate in MuJoCo.
3. Estimate future affordance by rolling out or analytically checking a distribution of possible next targets from the resulting state.
4. Define debt as loss of future reachable target count plus balance-margin degradation and recovery cost.
5. Select the posture minimizing current reach error, failure risk, torque effort, and estimated debt.

The method must store raw rollout rows, per-candidate debt estimates, aggregate metrics, ablations, pairwise comparisons, and plots.

## Baselines

Compare against:

- `random_posture`: random candidate.
- `arm_only_reach`: arm posture with minimal torso/base motion.
- `greedy_reach_mpc`: minimize immediate end-effector error only.
- `comfort_regularized_mpc`: immediate reach plus posture/torque comfort.
- `robust_balance_mpc`: immediate reach plus worst-case balance/perturbation margin.
- `affordance_debt_mpc`: proposed future-affordance debt method.
- `oracle_two_step_mpc`: upper bound with access to the actual next target.

The proposed method must beat non-oracle baselines on sequential success and energy under held-out stress to support the claim.

## Ablations

Run on combined stress:

- Full `affordance_debt_mpc`.
- No future affordance term.
- No balance-margin term.
- No recovery simulation.
- No torque/comfort term.
- Small future-target sample.
- Current-target-only oracle-like greedy.

The claim only survives if removing the future-affordance/debt term hurts sequential success or debt metrics.

## Statistical Plan

Report:

- At least five seeds.
- Per-seed/split success, immediate success, future success, energy, debt, and failure rates.
- 95% confidence intervals.
- Paired comparisons against every baseline on matched seed/split/episode tasks.
- Explicit negative cases and oracle gaps.

## Execution Stages

1. Replace the synthetic runner with a real MuJoCo articulated-body benchmark.
2. Run a tiny smoke test for contact stability and CSV schemas.
3. Run the full multi-seed benchmark.
4. Generate plots and pairwise statistics.
5. Rewrite the paper from archive memo to evidence-bearing draft.
6. Copy only `C:\Users\wangz\Downloads\65.pdf`.
7. Update child docs and parent batch reports.
8. Commit and push the public GitHub repo.

## Terminal Decision Rules

Mark `SUBMISSION_READY_CANDIDATE` only if:

- The proposed method beats all non-oracle baselines on most held-out/stress splits.
- Ablations show future-affordance debt is necessary.
- Oracle gap is reasonable.
- Failure modes and limitations are honest.
- Reproducibility artifacts are complete.

Mark `STRONG_REVISE` if:

- Real evidence exists and the mechanism helps against weak baselines, but it does not clear robust baselines, lacks hardware/public benchmark validation, or ablations are inconclusive.

Mark `KILL_ARCHIVE` if:

- The method fails greedy/robust baselines, the debt estimate is not predictive, or the benchmark cannot produce stable real evidence.

## Required Final Artifacts

- `src/run_experiment.py`: real MuJoCo implementation.
- `results/*.csv`: raw rollouts, metrics, ablations, pairwise tests.
- `figures/*.png`: paper-specific plots.
- `docs/paper65_terminal_evidence.md`: final decision and evidence.
- `paper/main.tex`: rebuilt paper or honest terminal archive.
- `C:\Users\wangz\Downloads\65.pdf`: numbered PDF in Downloads only.
- Public GitHub repository updated at `https://github.com/Jason-Wang313/65_humanoid_whole_body_affordance_debt`.

