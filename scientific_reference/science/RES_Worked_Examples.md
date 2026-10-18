# Actual FCS → RAS → RES calculations

Release: `sonar-science-v1.0-s7s10`. S7/S10 only. Current scientific conclusions are in the `*_Final_Report.md` files and this release's `science/` documents. Historical v4/v3 documents and tables are retained as provenance.

Common equation: `g(A) = 0.500091476458275 + 0.491368713316119 A + 0.366037234211599 max(0, A - 0.5)`. Full context: `models/context_profiles/context_v1.json`.

## S7_90B: corrected reference input 75% AC by mass
Raw file: `inputs/S7/90B.fcs`; SHA-256 `eb0e7f1f92db6b640cbf4212215a3ce4ad53a2bba9ecf75afcf4ddc138191db9`. Original acquisition ID is retained even when its label was corrected. Independent experimental unit: `S7_90B_well`.

Recorded events 100,000 → after acquisition QC 100,000 → cells 72,778 → singlets 66,477 → reporter population 32,207. Each selected event subtracts the saved linear backgrounds (green 2999.921288652426, red 1149.481510590721); the red threshold is applied to raw red values, and signed green values remain.

Corrected green sum = 5599302927.21647; corrected red sum = 5855417323.59827; RAS = 5599302927.22 / 5855417323.6 = **0.956260266**. Event-plus-shared-control RAS interval: [0.948752783, 0.964186991]. Effective red support: 3620.4, distinct from one independent well.

Frozen inverse calculation: `0.5 + (0.956260265968 - 0.745775833116) / 0.857405947528` = **0.745489821**, or **74.549% AC DNA mass equivalent**. Conditional bootstrap interval: [73.272%, 75.847%], based on 1000/1000 invertible draws. Broader compatibility interval: [65.2%, 84.1%], not a nominal 95% CI. The measurement-expanded primary/isotonic union has total width 20.8pp. Status: `PRIMARY_INFORMATIVE_CROSS_MODEL_SET_BROAD`; `S7_SAME_EXPERIMENT_INTERNAL_EXPLORATORY`. This is a model-derived equivalent, not measured RNA editing and not an independent held-out validation sample.

Run: `python science.py example --sample S7_90B --output _work/S7_90B.json`.

## S7_5B: corrected reference input 5% AC by mass
Raw file: `inputs/S7/5B.fcs`; SHA-256 `15bb9fc76b601e04968ea434aecd6712c2e2d7f3054acf1431539828920eb698`. Original acquisition ID is retained even when its label was corrected. Independent experimental unit: `S7_5B_well`.

Recorded events 100,000 → after acquisition QC 100,000 → cells 79,418 → singlets 74,152 → reporter population 25,884. Each selected event subtracts the saved linear backgrounds (green 2999.921288652426, red 1149.481510590721); the red threshold is applied to raw red values, and signed green values remain.

Corrected green sum = 1893239123.06276; corrected red sum = 3725591888.40726; RAS = 1893239123.06 / 3725591888.41 = **0.508171367**. Event-plus-shared-control RAS interval: [0.500489122, 0.515459696]. Effective red support: 3941.6, distinct from one independent well.

Frozen inverse calculation: `(0.508171367066 - 0.500091476458) / 0.491368713316` = **0.016443641**, or **1.644% AC DNA mass equivalent**. Conditional bootstrap interval: [0.208%, 4.255%], based on 860/1000 invertible draws. Broader compatibility interval: [0.0%, 17.6%], not a nominal 95% CI. The measurement-expanded primary/isotonic union has total width 21.8pp. Status: `NUMERICALLY_AVAILABLE_WEAK_OR_BOUNDARY_SUPPORT`; `S7_SAME_EXPERIMENT_INTERNAL_EXPLORATORY`. This is a model-derived equivalent, not measured RNA editing and not an independent held-out validation sample.

Run: `python science.py example --sample S7_5B --output _work/S7_5B.json`.

## S7_100A: corrected reference input 100% AC by mass
Raw file: `inputs/S7/100A.fcs`; SHA-256 `a4adb9faa119bd4d645ff9a570a8673d505e7815da1f07ff9c575663210cdd5d`. Original acquisition ID is retained even when its label was corrected. Independent experimental unit: `S7_100A_well`.

Recorded events 100,000 → after acquisition QC 100,000 → cells 76,566 → singlets 70,179 → reporter population 29,732. Each selected event subtracts the saved linear backgrounds (green 2999.921288652426, red 1149.481510590721); the red threshold is applied to raw red values, and signed green values remain.

Corrected green sum = 5057803455.078; corrected red sum = 4417852785.51276; RAS = 5057803455.08 / 4417852785.51 = **1.144855589**. Event-plus-shared-control RAS interval: [1.134496293, 1.155069211]. Effective red support: 3046.0, distinct from one independent well.

Frozen inverse calculation: `0.5 + (1.1448555895 - 0.745775833116) / 0.857405947528` = **0.965450184**, or **96.545% AC DNA mass equivalent**. Conditional bootstrap interval: [95.012%, 98.567%], based on 1000/1000 invertible draws. Broader compatibility interval: [86.7%, 100.0%], not a nominal 95% CI. The measurement-expanded primary/isotonic union has total width 17.1pp. Status: `OBSERVED_HIGH_END_FLATTENING_PRIMARY_SLOPE_MODEL_DEPENDENT`; `S7_SAME_EXPERIMENT_INTERNAL_EXPLORATORY`. This is a model-derived equivalent, not measured RNA editing and not an independent held-out validation sample.

Run: `python science.py example --sample S7_100A --output _work/S7_100A.json`.

The low-input example shows boundary sensitivity and missing bootstrap inverses; the 100% example shows why a positive fitted slope is not proof of resolving the observed 90–100% plateau. `S7_90B` is the informative corrected 75% example. JSON report output also includes a null PER and its reason.
