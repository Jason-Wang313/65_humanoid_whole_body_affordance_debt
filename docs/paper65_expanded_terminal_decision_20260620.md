# Paper 65 Expanded-Standard Terminal Decision

Date: 2026-06-20

Decision: `KILL_ARCHIVE`

## Evidence Scale

- Main raw rows: 21,120.
- Ablation raw rows: 4,992.
- Main split-method summaries: 110.
- Seed-level summaries: 880.
- Paired comparisons: 100.

## Aggregate Result

- BAR-MPC aggregate sequential success: 0.496.
- BAR-MPC aggregate energy: 0.400.
- BAR-MPC is not cleanly separated from greedy, robust balance, future-distribution, or learned-linear debt baselines.

## Why This Is Not ICLR-Main Ready

- The strong-baseline gate fails.
- The no-online variant is identical to BAR-MPC in the frozen implementation.
- Future-debt and tail-debt ablations match BAR-MPC on at least one hostile split.
- Hostile splits expose first-choice differences but not a reliable outcome advantage.

## Artifact Rule

- The final PDF must remain `C:\Users\wangz\Downloads\65.pdf` only.
- No PDF should be placed on the visible Desktop.
