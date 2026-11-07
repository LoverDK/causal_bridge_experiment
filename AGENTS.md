# Reviewer-guided experiment rebuilding

This repository is a local revision workspace for the Causal ATLAS paper.

- Before advancing any experiment, read `revision/REVIEW_TRACKER.md`, `revision/review_tracker.json`, and the current experiment protocol. Start with `revision/FIRST_WORKFLOW.md`.
- Associate each experiment with specific reviewer concerns, admissible inputs, assumptions, comparators, and an expected or falsifiable outcome before execution.
- After every experimental milestone, revisit the complete concern list. Record evidence, what it supports, what it cannot establish, and any justified status changes. Preserve previous statuses for concerns not investigated.
- A successful run is evidence of execution, not proof that a reviewer concern is resolved. Distinguish reproduction, partial evidence, a supported response, and unresolved work.
- Explain one experimental unit and its decisions before scaling to aggregate results. Keep the author's understanding of the design and interpretation part of the workflow.
- Preserve the published inputs, configurations, and result archive. Use fresh output directories and record code versions, seeds, commands, and evidence paths.
- Before starting each experiment, tell the author the estimated wall-clock duration range, the measurement or scaling basis, and whether CPU, GPU, memory, or I/O is the bottleneck. Estimate smoke runs too; use their measured throughput to revise the full-run estimate. For a long run, give the author an opportunity to choose a rented instance before launch. Record estimates and actual durations; do not infer that a GPU will accelerate CPU-only numerical code.
- Distinguish the current method, its variants, baselines, and legacy prototypes. State when an interval is an outer region or a predictive interval rather than the theorem's sharp region or certificate.
- Do not attribute the log-determinant theorem to the prospective-radius bridge heuristic. Do not apply the design-only radius to weights selected from the same evaluation outcomes.
- Do not treat synthetic mechanism labels or known smoothness constants as real-world calibration. Do not change thresholds or selectively report scenarios to manufacture favorable results.
- Keep the writing task separate from experimental conclusions. The original Overleaf `01.tex` is preserved; its humanized copy must retain mathematical meaning, factual results, citations, and scope.
