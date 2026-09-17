# Many Labs 2 independent-source benchmark

## Audited design

- Public source: Many Labs 2 official OSF-linked GitHub repository, commit `acef63fc397b8dce7f0b00f863bcea78d324bea8`.
- Experiment: Tversky--Kahneman framing replication (`Tversky.1`).
- Binary treatment: `Cheap` (A=1) versus `Expensive` (A=0) price context.
- Binary outcome: willingness to travel to another store (`Yes`=1, `No`=0).
- Independent unit for transport: the Many Labs 2 `source` sample.
- Estimand: source-specific risk difference Pr(Yes | Cheap) - Pr(Yes | Expensive).
- Split: strict leave-one-source-out; the held-out outcome and effect are not used for fitting or release/refusal.

The cleaned file contains 57 complete sources and 7,228 analyzed responses. The
commit-pinned input has SHA-256 `15898b5c241696adc7fd91a638839ba49a9f9be64c78da9151b39018d66bfbd3`.

## Aggregate estimates

- Fixed-effect mean risk difference: 0.1728 (SE 0.0108).
- DerSimonian--Laird random-effects mean: 0.1729 (SE 0.0108).
- Estimated between-source SD: 0.0051; I-squared: 0.4%;
  Cochran Q p-value: 0.4667.

## Held-out prediction

| Method | Release rate | MAE | RMSE | 95% PI coverage | Mean PI width |
|---|---:|---:|---:|---:|---:|
| Fixed effects, always release | 1.000 | 0.0800 | 0.0961 | 0.982 | 0.4041 |
| Random effects, always release | 1.000 | 0.0801 | 0.0961 | 0.982 | 0.4149 |
| Random effects, release only if half-width <= 0.15 | 0.105 | 0.0489 | 0.0522 | 1.000 | 0.2374 |

## Interpretation boundary

These are real independent-source predictions, but the random-effects interval is only a model-based baseline.
It is not a finite-sample-valid certificate, the tolerance was not learned from target outcomes, and the observed
held-out risk difference is itself noisy. This benchmark therefore supports claims about the need for selective
transport and provides a leakage-free test bed; it does not by itself validate calibrated mechanism uncertainty
sets or the paper's strongest coverage theorem.
