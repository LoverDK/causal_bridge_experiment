# Weight and Geometry Attribution Experiments

Profile: ablations_full; independent worlds: 1800.

Post-review paired analysis on the existing synthetic DGP. These results do not compare ExAtlas.
All bounds are valid under the declared model; local optimization is not globally certified.
Common random and nearest acquisition prefixes isolate weights and envelopes. Each variant stops independently.
Certificate guarantees are per policy, not simultaneous across all methods or conditional on release.

## Final Stopped Outcomes

| Scenario | Schedule | Certificate | Tolerance | Variant | Release % | Participants | Path coverage % | Bad release % | Released MAE |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| bridgeable | nearest | r2 | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | optimized__barycentric | 100.00 | 241.60 | 100.00 | 0.00 | 0.0471 |
| bridgeable | nearest | r2 | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | optimized__minimum | 100.00 | 241.60 | 100.00 | 0.00 | 0.0471 |
| bridgeable | nearest | r2 | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | r2 | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | nearest | rinf | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.2 | optimized__barycentric | 38.50 | 261.44 | 100.00 | 0.00 | 0.0330 |
| bridgeable | random | r2 | 0.3 | optimized__barycentric | 100.00 | 159.68 | 100.00 | 0.00 | 0.0399 |
| bridgeable | random | r2 | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | r2 | 0.2 | optimized__minimum | 38.50 | 261.44 | 100.00 | 0.00 | 0.0330 |
| bridgeable | random | r2 | 0.3 | optimized__minimum | 100.00 | 159.68 | 100.00 | 0.00 | 0.0399 |
| bridgeable | random | r2 | 0.2 | uniform__minimum | 1.33 | 288.00 | 100.00 | 0.00 | 0.0382 |
| bridgeable | random | r2 | 0.3 | uniform__minimum | 20.33 | 283.52 | 100.00 | 0.00 | 0.1065 |
| bridgeable | random | rinf | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | optimized__barycentric | 31.83 | 244.96 | 100.00 | 0.00 | 0.0403 |
| bridgeable | random | rinf | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | optimized__minimum | 31.83 | 244.96 | 100.00 | 0.00 | 0.0403 |
| bridgeable | random | rinf | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| bridgeable | random | rinf | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| supported | nearest | r2 | 0.2 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | nearest | r2 | 0.3 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | nearest | r2 | 0.2 | nearest_source__minimum | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | nearest | r2 | 0.3 | nearest_source__minimum | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | nearest | r2 | 0.2 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | nearest | r2 | 0.3 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | nearest | r2 | 0.2 | optimized__lipschitz | 9.00 | 267.52 | 100.00 | 0.00 | 0.0173 |
| supported | nearest | r2 | 0.3 | optimized__lipschitz | 100.00 | 0.00 | 100.00 | 0.00 | 0.0160 |
| supported | nearest | r2 | 0.2 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | nearest | r2 | 0.3 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | nearest | r2 | 0.2 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | nearest | r2 | 0.3 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | nearest | rinf | 0.2 | inverse_variance__minimum | 77.67 | 64.32 | 100.00 | 0.00 | 0.0151 |
| supported | nearest | rinf | 0.3 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | nearest | rinf | 0.2 | nearest_source__minimum | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | nearest | rinf | 0.3 | nearest_source__minimum | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | nearest | rinf | 0.2 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | nearest | rinf | 0.3 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | nearest | rinf | 0.2 | optimized__lipschitz | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | nearest | rinf | 0.3 | optimized__lipschitz | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | nearest | rinf | 0.2 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | nearest | rinf | 0.3 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | nearest | rinf | 0.2 | uniform__minimum | 77.67 | 64.32 | 100.00 | 0.00 | 0.0151 |
| supported | nearest | rinf | 0.3 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | r2 | 0.2 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | r2 | 0.3 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | r2 | 0.2 | nearest_source__minimum | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | random | r2 | 0.3 | nearest_source__minimum | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | random | r2 | 0.2 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | random | r2 | 0.3 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | random | r2 | 0.2 | optimized__lipschitz | 6.50 | 275.20 | 100.00 | 0.00 | 0.0165 |
| supported | random | r2 | 0.3 | optimized__lipschitz | 100.00 | 0.00 | 100.00 | 0.00 | 0.0160 |
| supported | random | r2 | 0.2 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | random | r2 | 0.3 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0153 |
| supported | random | r2 | 0.2 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | r2 | 0.3 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | rinf | 0.2 | inverse_variance__minimum | 78.83 | 62.24 | 100.00 | 0.00 | 0.0150 |
| supported | random | rinf | 0.3 | inverse_variance__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| supported | random | rinf | 0.2 | nearest_source__minimum | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | random | rinf | 0.3 | nearest_source__minimum | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | random | rinf | 0.2 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | random | rinf | 0.3 | optimized__barycentric | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | random | rinf | 0.2 | optimized__lipschitz | 0.17 | 287.52 | 100.00 | 0.00 | 0.0309 |
| supported | random | rinf | 0.3 | optimized__lipschitz | 99.50 | 1.44 | 100.00 | 0.00 | 0.0666 |
| supported | random | rinf | 0.2 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | random | rinf | 0.3 | optimized__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0192 |
| supported | random | rinf | 0.2 | uniform__minimum | 77.67 | 64.32 | 100.00 | 0.00 | 0.0151 |
| supported | random | rinf | 0.3 | uniform__minimum | 100.00 | 0.00 | 100.00 | 0.00 | 0.0149 |
| unreachable | nearest | r2 | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | r2 | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | nearest | rinf | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | r2 | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | inverse_variance__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | nearest_source__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | optimized__barycentric | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | optimized__lipschitz | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | optimized__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.2 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |
| unreachable | random | rinf | 0.3 | uniform__minimum | 0.00 | 288.00 | 100.00 | 0.00 | NA |

## Paired Differences

Direction: optimized minimum minus comparator. Negative cost difference favors the reference.
Intervals are individual exploratory 95% stratified paired bootstrap intervals, not familywise claims.

| Schedule | Certificate | Tolerance | Comparator | Metric | Difference | 95% interval |
|---|---|---|---|---|---:|---|
| nearest | r2 | 0.2 | inverse_variance__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | inverse_variance__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | nearest_source__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | nearest_source__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | optimized__lipschitz | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | optimized__lipschitz | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | uniform__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.2 | uniform__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.3 | inverse_variance__minimum | released | 1.0000 | [1.0000, 1.0000] |
| nearest | r2 | 0.3 | inverse_variance__minimum | new_n | -46.4000 | [-50.2400, -42.5600] |
| nearest | r2 | 0.3 | nearest_source__minimum | released | 1.0000 | [1.0000, 1.0000] |
| nearest | r2 | 0.3 | nearest_source__minimum | new_n | -46.4000 | [-50.0840, -42.0800] |
| nearest | r2 | 0.3 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.3 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | r2 | 0.3 | optimized__lipschitz | released | 1.0000 | [1.0000, 1.0000] |
| nearest | r2 | 0.3 | optimized__lipschitz | new_n | -46.4000 | [-50.2400, -42.7200] |
| nearest | r2 | 0.3 | uniform__minimum | released | 1.0000 | [1.0000, 1.0000] |
| nearest | r2 | 0.3 | uniform__minimum | new_n | -46.4000 | [-50.0800, -42.5600] |
| nearest | rinf | 0.2 | inverse_variance__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | inverse_variance__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | nearest_source__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | nearest_source__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | optimized__lipschitz | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | optimized__lipschitz | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | uniform__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.2 | uniform__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | inverse_variance__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | inverse_variance__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | nearest_source__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | nearest_source__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | optimized__lipschitz | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | optimized__lipschitz | new_n | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | uniform__minimum | released | 0.0000 | [0.0000, 0.0000] |
| nearest | rinf | 0.3 | uniform__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| random | r2 | 0.2 | inverse_variance__minimum | released | 0.3850 | [0.3600, 0.4100] |
| random | r2 | 0.2 | inverse_variance__minimum | new_n | -26.5600 | [-29.7600, -23.2000] |
| random | r2 | 0.2 | nearest_source__minimum | released | 0.3850 | [0.3617, 0.4100] |
| random | r2 | 0.2 | nearest_source__minimum | new_n | -26.5600 | [-29.9200, -23.3600] |
| random | r2 | 0.2 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| random | r2 | 0.2 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| random | r2 | 0.2 | optimized__lipschitz | released | 0.3850 | [0.3583, 0.4084] |
| random | r2 | 0.2 | optimized__lipschitz | new_n | -26.5600 | [-29.9200, -23.2000] |
| random | r2 | 0.2 | uniform__minimum | released | 0.3717 | [0.3450, 0.3983] |
| random | r2 | 0.2 | uniform__minimum | new_n | -26.5600 | [-29.7600, -23.3600] |
| random | r2 | 0.3 | inverse_variance__minimum | released | 1.0000 | [1.0000, 1.0000] |
| random | r2 | 0.3 | inverse_variance__minimum | new_n | -128.3200 | [-132.6400, -124.0000] |
| random | r2 | 0.3 | nearest_source__minimum | released | 1.0000 | [1.0000, 1.0000] |
| random | r2 | 0.3 | nearest_source__minimum | new_n | -128.3200 | [-132.6400, -123.8400] |
| random | r2 | 0.3 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| random | r2 | 0.3 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| random | r2 | 0.3 | optimized__lipschitz | released | 1.0000 | [1.0000, 1.0000] |
| random | r2 | 0.3 | optimized__lipschitz | new_n | -128.3200 | [-132.8000, -123.8400] |
| random | r2 | 0.3 | uniform__minimum | released | 0.7967 | [0.7700, 0.8233] |
| random | r2 | 0.3 | uniform__minimum | new_n | -123.8400 | [-128.3200, -119.3600] |
| random | rinf | 0.2 | inverse_variance__minimum | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | inverse_variance__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | nearest_source__minimum | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | nearest_source__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | optimized__lipschitz | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | optimized__lipschitz | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | uniform__minimum | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.2 | uniform__minimum | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.3 | inverse_variance__minimum | released | 0.3183 | [0.3050, 0.3300] |
| random | rinf | 0.3 | inverse_variance__minimum | new_n | -43.0400 | [-46.5600, -39.5200] |
| random | rinf | 0.3 | nearest_source__minimum | released | 0.3183 | [0.3050, 0.3317] |
| random | rinf | 0.3 | nearest_source__minimum | new_n | -43.0400 | [-46.5600, -39.3600] |
| random | rinf | 0.3 | optimized__barycentric | released | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.3 | optimized__barycentric | new_n | 0.0000 | [0.0000, 0.0000] |
| random | rinf | 0.3 | optimized__lipschitz | released | 0.3183 | [0.3050, 0.3300] |
| random | rinf | 0.3 | optimized__lipschitz | new_n | -43.0400 | [-46.5600, -39.3600] |
| random | rinf | 0.3 | uniform__minimum | released | 0.3183 | [0.3033, 0.3300] |
| random | rinf | 0.3 | uniform__minimum | new_n | -43.0400 | [-46.4000, -39.6800] |

## Files

`records.csv`: all stopped outputs. `plans.jsonl`: all fixed-budget weights and counterfactual scores.
`fixed_budget_summary.csv` and `stopped_summary.csv`: distinguish common-budget widths from refused-output widths.
`same_weight_geometry.csv`: envelope gaps with exactly the same optimized-minimum weights.
`paired_differences.csv`: all scenarios and both evaluation regimes; `stopped_cells.csv`: unpooled surfaces.
No-release conditional MAEs remain missing. No negative results are omitted.
