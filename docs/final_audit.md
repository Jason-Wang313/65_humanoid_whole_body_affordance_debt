# Final Audit

1. Chosen thesis: Humanoid Whole-Body Affordance Debt explores `Measure and minimize future affordance loss induced by current whole-body posture choices.` for humanoid whole-body manipulation.
2. ICLR-main decision: KILL_ARCHIVE.
3. Submission-hardening version: v4 real MuJoCo rebuild.
4. Reason: real articulated whole-body evidence falsifies the mechanism; affordance-debt MPC is matched by greedy/comfort/robust/no-debt baselines.
5. Closest hostile prior work: see `docs/hostile_prior_work.md`, `docs/hostile_prior_work_100_cards.csv`, and `docs/hostile_reviewer_response.md`.
6. Reproducibility: `python src/run_experiment.py` reproduces the MuJoCo benchmark, metrics, ablations, pairwise tests, and figures.
7. Claim-validity status: main-conference claims killed by real negative evidence.
8. Exact Downloads PDF path: `C:/Users/wangz/Downloads/65.pdf`
9. GitHub URL: https://github.com/Jason-Wang313/65_humanoid_whole_body_affordance_debt
10. Confirmation: no visible Desktop copy was requested or made.

## 2026-06-15 Continuation Audit

Executed `docs/paper65_iclr_submission_execution_plan_20260615.md`.

Additional verification:
- Python compile passed for `src/run_experiment.py`.
- CSV finite/schema audit passed for main, paired, ablation, seed, stress, and negative-case result files.
- LaTeX/BibTeX/PDF rebuild completed with bibliography key hygiene fixed and `C:/Users/wangz/Downloads/65.pdf` refreshed.
- `C:/Users/wangz/Desktop/65.pdf` is absent.
- Stale hostile-review wording was corrected to state that current `KILL_ARCHIVE` rests on real negative evidence.

Decision remains `KILL_ARCHIVE`, not ICLR-main-ready. See `docs/paper65_terminal_audit_20260615.md`.
