# Frozen four-layer definitions
| Layer | Name | Function | Output and unit |
| --- | --- | --- | --- |
| 0 | Context Calibration | Decode linear channels; apply acquisition, scatter/singlet selection; estimate background and distinct fluorescence thresholds; declare QC and compatibility | Versioned Context Profile; detector a.u. and event counts |
| 1 | Flow Quantification | Ratio of paired corrected sums in a declared population | RAS, dimensionless channel ratio |
| 2 | Reporter Calibration | Invert an empirical reference response g(A) | RES — Relative Editing Score; operational label AC Reference-Equivalent Score; AC DNA mass-equivalent fraction |
| 3 | Biological Calibration | Evaluate independent molecular evidence and qualify any future h(RES) | Relative molecular index now; PER=100*h(RES) percent only after qualified absolute RNA calibration |

RAS_P=sum(g_i)/sum(r_i); P_R=V∩R_q+; P_RB=V∩R_q+∩B+ only with linked editor present. V is acquisition-QC/scatter/singlet-selected events, not a viability-marker-defined live population. Display transformations do not enter sums. Distinguish repeatability, reference recovery, molecular accuracy, computational reproducibility and external transfer.
