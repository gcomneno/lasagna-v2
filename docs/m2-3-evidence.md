# M2.3 — Candidate evaluation evidence

Date: 2026-10-02

Evidence status: VALID

Evidence type: observational, non-normative

Source corpus commit:
`cf81bd9df0f9b5480fa6e4183397870ccf668f5a`

Protocol revision used for evaluation:
`2.0`

## Purpose

This file records the executed M2.3 candidate-layout evaluation.

It does not redefine the frozen selection methodology.

It does not alter candidate admissibility thresholds.

It does not reopen candidate selection.

No V2 production bytes were emitted during this evaluation.

## Canonical corpus identity

- cases: 1575
- reference files: 1575
- reference segments: 11700
- qualifying segments: 8219
- qualifying MEAN: 999
- qualifying LINEAR: 3900
- qualifying RW: 3320
- reference stream SHA256: `9d2d447a800fc3b5de50b1bc1eb3d3e4d4e64b1a47e412afa641bcb8e1a3ed92`
- corpus manifest SHA256: `20e69077397efe73815d5c594d1ef94281f7777d9bd8c861c0db34a9e55f03dc`
- reference-segments SHA256: `ae4d9cd6e48640d29ac856333b7d47d2da5714abdced3ae1b2d476877a05ba8a`

## Reference-control integrity

- L52 reference residual match: 8219/8219
- L52 reference decode match: 8219/8219
- Criterion A gate: PASS

The L52 control reproduced both frozen V1 residuals and frozen V1
reconstruction on every qualifying segment.

## Candidate results

| Candidate | Entry bytes | A max f32 ULP error | B p99 max | C p99 max | R_select | Residual-change fraction | Varint-class-change fraction | Admissible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| L32 | 32 | 0.49998410046100616 | 1.3273705672169306e-05 | 0 | 12.248895434462446 | 4.7193556506418324e-06 | 0 | YES |
| L40_PRED64 | 40 | 0.49998410046100616 | 1.2274940434549675e-05 | 0 | 13.021421877091981 | 1.5731185502139442e-06 | 0 | YES |
| L40_QSEED64 | 40 | 0.49997424520552158 | 1.3264907499698281e-05 | 0 | 13.021421877091981 | 4.7193556506418324e-06 | 0 | YES |
| L52 | 52 | 0 | 0 | 0 | 14.180211541036284 | 0 | 0 | YES |

## L32 stratum evidence

Criterion B:

- B_P99_MEAN = 1.197105896177462e-05
- B_P99_LINEAR = 1.3273705672169306e-05
- B_P99_RW = 1.2274940434549675e-05
- B_P99_MAX = 1.3273705672169306e-05

Criterion C:

- C_P99_MEAN = 0
- C_P99_LINEAR = 0
- C_P99_RW = 0
- C_P99_MAX = 0

Measured comparable rate:

- RATE_BPS_MEAN = 10.75
- RATE_BPS_LINEAR = 13.107142857142858
- RATE_BPS_RW = 12.889543446244478
- R_SELECT = 12.248895434462446

## Frozen selection

All four candidates were admissible.

Primary selection rule:

`MIN_R_SELECT_EQUAL_STRATUM_WEIGHT`

Observed R_select ordering:

1. L32 = 12.248895434462446
2. L40_PRED64 = 13.021421877091981
3. L40_QSEED64 = 13.021421877091981
4. L52 = 14.180211541036284

The canonical fallback tie-break was not required to select the winner.

M2_3_WINNER = L32

M2_3_OUTCOME = L32

M2_3_EVALUATION_GATE = PASS

## Execution boundary

READ_ONLY_POSTCONDITION = PASS

V2_BYTES_EMITTED = NO

PROTOCOL_MUTATION = NO

SELECTION_REOPENED = NO

M2.3 is complete.

The next normative action is M2.4 physical freeze of the already selected
L32 layout. M2.4 SHALL consume this result; it SHALL NOT rerun or reinterpret
candidate selection.
