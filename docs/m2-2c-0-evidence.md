# M2.2C.0 — In-memory frozen corpus execution evidence

Date: 2026-10-02

Evidence status: VALID

Evidence type: observational, non-normative

Source HEAD: `5313625e29cd47c9b69cbd9b5b8fc91f0f39b589`

Protocol revision: M2.2B v1.2

Protocol manifest SHA256:
`dff3213bebe45666ac8254d01fa88b230cad4a535e5ed2b03210441bcbc5399e`

## Purpose

This artifact records the result of the first valid M2.2C.0 in-memory
execution under the frozen M2.2B v1.2 methodology.

It does not modify the methodology, corpus definition, qualification rules,
coverage thresholds, candidate set, selection rules, or reference encoder.

No canonical M2.3 corpus was materialized.

No L32, L40_PRED64, L40_QSEED64 or L52 candidate was evaluated.

## Preceding verifier recovery

The first M2.2C.0 execution stopped before scientific interpretation because
the harness parsed a canonical case ID using an incorrect colon-field count.

Observed canonical ID:

`lasagna2:m2.3:v1:mean_stationary_v1:b=-10:l=0:r=0`

Failure classification:

- CONTRACT_GAP = NO
- VERIFIER_BUG = YES
- HARNESS_ALIAS = NO
- VERIFIER_POLICY = NO

The recovery changed only the case-ID parser, replacing the incorrect
split-count assumption with the frozen case-ID grammar.

The normative methodology was not changed.

## Determinism evidence

- PYTHONHASHSEED runs: 1, 2
- reference cases: 1575
- reference stream bytes: 1981816
- reference stream SHA256:
  `ca8ee6604ce65957331c22ac4617ae1ae56f0065cda4e3b1dd30552929e1fa46`
- cross-process byte identity: 1575 / 1575
- reference determinism gate: PASS

The compared object was the framed stream containing the actual V1 encoded
bytes for every case, not merely a collection of per-case hashes.

## Historical D1 reference evidence

Historical inputs and frozen SHA256 values:

- `trend.csv`
  - SHA256:
    `1cb13a9c80b2a9944b1eb13c18472972e695895b409bb217171f56166d420746`
  - samples: 200
  - reference segments: 2

- `sine_noise.csv`
  - SHA256:
    `e555b47912504c4405806c97f6d50ff408ef9201e0ef1904de7704ccecb4362e`
  - samples: 300
  - reference segments: 6

- `flat_spike.csv`
  - SHA256:
    `9a429b08d1abb3f2b53afde333248fb0ad7b2685f44608633c4b666b1b8c39be`
  - samples: 300
  - reference segments: 4

Reference D1 segment strata:

- MEAN: 2
- LINEAR: 6
- RW: 4

Active D1 metadata observation counts:

- mean: 2
- slope: 6
- intercept: 6
- Q: 12
- seed: 4

No observed active D1 value was zero.

## Frozen corpus execution

Total cases:

`1575`

Case length:

`512`

Total reference samples:

`806400`

Total reference segments:

`12012`

Actual V1 wire predictor distribution:

- RAW_MEAN = 2806
- RAW_LINEAR = 8818
- RAW_RW = 388

Generator to actual V1 wire stratum:

| Generator | MEAN | LINEAR | RW |
| --- | ---: | ---: | ---: |
| mean_stationary_v1 | 1811 | 2089 | 0 |
| linear_trend_v1 | 564 | 3335 | 1 |
| random_walk_v1 | 431 | 3394 | 387 |

Generator labels therefore do not determine the normative stratum.
The normative stratum is the `predictor_type` actually stored in the V1 wire.

## Qualifying coverage

Frozen minimum coverage:

- each MEAN / LINEAR / RW stratum: >= 500 qualifying segments
- total: >= 1500 qualifying segments

Observed qualifying coverage:

- COVERAGE_MEAN = 572
- COVERAGE_LINEAR = 8109
- COVERAGE_RW = 342
- TOTAL_QUALIFYING_SEGMENTS = 9023

Generator to qualifying V1 wire stratum:

| Generator | MEAN | LINEAR | RW |
| --- | ---: | ---: | ---: |
| mean_stationary_v1 | 482 | 1889 | 0 |
| linear_trend_v1 | 5 | 3335 | 1 |
| random_walk_v1 | 85 | 2885 | 341 |

Non-qualification counts:

- LENGTH_LT_10 = 10
- INVALID_PREDICTOR = 0
- ACTIVE_METADATA_NONFINITE = 0
- Q_INVALID = 0
- OUTSIDE_D1_UNION_D2 = 2979

## Structural undercoverage proof

The decisive result exists before D1/D2 qualification:

`RAW_RW = 388`

while the frozen qualifying requirement is:

`RW >= 500`

Therefore even the maximally favorable hypothetical condition in which every
raw RW segment qualified would provide only:

`388 < 500`

Raw RW structural deficit:

`500 - 388 = 112`

Observed qualifying RW deficit:

`500 - 342 = 158`

Consequently, modifying D1/D2 qualification alone cannot make this frozen
corpus satisfy the RW coverage requirement.

## Decision

`COVERAGE_DECISION = INCONCLUSIVE`

`UNDERCOVERED_STRATA = RW`

`M2_2C_0_OUTCOME = INCONCLUSIVE`

The result is scientifically valid but insufficient to authorize candidate
evaluation.

Frozen anti-adaptation rules remain in force:

- SEED_SHOPPING_PERMITTED = NO
- RETRY_WITH_ADDITIONAL_CASES = NO
- threshold relaxation = NO
- post-result candidate invention = NO
- stratum removal = NO

## Authorization state

`M2_2C_MATERIALIZATION_AUTHORIZED = NO`

`M2_3_CANDIDATE_EVALUATION_AUTHORIZED = NO`

`CORPUS_GENERATION_AUTHORIZED = NO`

`CANONICAL_CORPUS_MATERIALIZED = NO`

`L32_EVALUATED = NO`

`L40_PRED64_EVALUATED = NO`

`L40_QSEED64_EVALUATED = NO`

`L52_EVALUATED = NO`

## Interpretation boundary

This checkpoint records evidence only.

It does not amend M2.2B v1.2 and does not reinterpret the frozen threshold.

Any future experiment that changes the frozen corpus construction,
generator behavior, grid, qualification semantics or coverage requirement
must proceed through the revision policy rather than being treated as a
retry of this execution.

M2.2C.0 under the frozen v1 methodology is complete with outcome
`INCONCLUSIVE`.
