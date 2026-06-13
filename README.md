# 65 Humanoid Whole-Body Affordance Debt

Submission-hardening version: v4 real-evidence rebuild

Terminal decision: KILL_ARCHIVE for ICLR main conference.

This version replaces the synthetic stress-test scaffold with a real MuJoCo articulated whole-body reaching benchmark. The benchmark tests whether penalizing future affordance debt improves sequential humanoid reach under support-width, high-target, lateral-target, weak-actuation, payload, and combined shifts.

The negative result is decisive: affordance-debt MPC improves over random and arm-only weak baselines, but greedy reach, comfort-regularized MPC, robust balance MPC, and no-debt ablations essentially match it. The mechanism is therefore not submission-ready and is archived.

## Reproduce Real Benchmark

```powershell
python src\run_experiment.py
```

Expected full run: 5 seeds, 12 episodes per seed/split/method, 7 stress splits, 7 main methods, and combined-shift ablations.

## Rebuild PDF

```powershell
cd paper
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Canonical local PDF: `C:/Users/wangz/Downloads/65.pdf`
