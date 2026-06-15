# Hostile Reviewer Response

Paper: 65 Humanoid Whole-Body Affordance Debt

Continuation audit date: 2026-06-15

## Strongest Technical Threats

- Whole-body humanoid manipulation and contact-posture planning.
- Robot-free demonstration systems for humanoid whole-body manipulation.
- Unified humanoid loco-manipulation policies and trajectory-centric humanoid learning.
- Robust balance/recovery planning and comfort-regularized whole-body MPC.

## ICLR Main Response

A hostile ICLR reviewer would no longer be correct to reject this paper for synthetic-only evidence. The v4 rebuild contains a real MuJoCo articulated-body benchmark, implemented affordance-debt scoring, paired baselines, stress splits, ablations, confidence intervals, figures, and a rebuilt PDF.

The reviewer would still be correct to reject the paper as an ICLR-main submission because the real evidence falsifies the current mechanism. Affordance-debt MPC is essentially matched by greedy reach, comfort-regularized MPC, robust balance MPC, and no-debt ablations. The future-debt term does not create a meaningful performance gap.

## Honest Action

The current terminal state is `KILL_ARCHIVE`. This is a real negative result, not merely an archive caused by missing simulator evidence.

## What Would Be Needed To Revive

- A substantially new future-affordance mechanism that changes first-posture selection.
- Clear gains over greedy, comfort, and robust balance baselines.
- Ablations proving the future-debt term is necessary.
- Hardware or public humanoid benchmark validation.
- Manual full-paper related-work synthesis.
