# Lasagna 2 — Rate-Distortion Design

> **Model structure only when structure pays for itself.**

This document defines the technical design philosophy that emerged from the
BANANA-GATE³ characterization of **Lasagna 2 — Time Series Predictive Codec**.

It does not replace the historical `manifesto.md`. The historical manifesto
records the conceptual origin of the project; this document defines the
engineering direction supported by the current measurements.

---

## 1. Core principle

Lasagna 2 is a predictive codec for structured, locally predictable time
series.

Prediction is not valuable merely because it reduces reconstruction error.

Segmentation, predictors, metadata and specialized residual representations
all have an encoded cost.

A model should therefore be introduced only when the benefit it provides
justifies that cost.

In short:

> **Model structure only when structure pays for itself.**

---

## 2. From descriptive modeling to economic modeling

The MVP primarily asks:

> How well can this segment be predicted?

A rate-aware encoder must instead ask:

> Is this representation cheaper, at the required reconstruction quality,
> than the available alternatives?

A better predictor is not automatically a better coding decision.

A new segment is not automatically useful because it lowers MSE.

A specialized residual codec is not automatically useful because it exploits
a particular statistical pattern.

Every additional structure must justify itself in the final encoded
representation.

---

## 3. Rate and distortion

The central optimization objective is expressed as:

```text
J = D + λR
```

where:

- `D` is reconstruction distortion;
- `R` is encoded rate or encoded representation cost;
- `λ` controls the relative cost assigned to rate.

A larger `λ` makes encoded size more expensive relative to distortion.

The encoder should compare candidate representations according to their
actual or accurately modeled rate-distortion cost rather than optimizing
distortion and rate independently.

---

## 4. Rate is not only residual payload

For Lasagna 2, the encoded rate must account for the complete representation:

```text
R =
    R_global
  + R_segment_metadata
  + R_block_metadata
  + R_predictor
  + R_residuals
```

In the current MVP, important components include:

- global file header and context;
- segment table entries;
- residual block headers;
- residual payload.

This distinction matters because a representation can reduce residual error
or residual magnitude while still increasing total encoded size.

---

## 5. Evidence from BANANA-GATE³

The M1 characterization exposed two important structural effects.

### 5.1 Segment metadata can dominate

For `sine_noise` in the measured MVP configuration:

```text
total file             870 B
segment table          384 B
residual block headers  72 B
residual payload       300 B
```

The segment table alone is larger than the residual payload.

This demonstrates that segmentation has a real economic cost.

Creating additional segments cannot therefore be justified solely by improved
prediction accuracy.

### 5.2 Quantization does not currently guarantee rate reduction

The `C_Q` sweep showed that reconstruction error changed substantially while
encoded size remained constant.

For the measured `sine_noise` cases:

```text
C_Q = 0.0625 -> 870 B
C_Q = 4      -> 870 B
```

while reconstruction distortion increased strongly.

The residual occupancy audit explained the plateau: all quantized residuals
still occupied one varint byte.

Therefore:

```text
smaller residual magnitude
    !=
smaller encoded rate
```

unless the residual representation can exploit the changed distribution.

---

## 6. Segmentation as an economic decision

The MVP segmentation logic is primarily prediction-oriented.

A future rate-aware segmentation strategy should evaluate whether splitting
a region actually decreases the global coding objective.

Conceptually:

```text
cost_without_split =
    distortion_without_split
  + λ * rate_without_split

cost_with_split =
    distortion_with_split
  + λ * rate_with_split
```

A split should be accepted only when:

```text
cost_with_split < cost_without_split
```

This naturally includes the additional cost of:

- another segment entry;
- another residual block;
- another predictor description;
- any additional representation overhead.

The key question becomes:

> Does the reduction in residual cost and/or distortion repay the structural
> cost of creating another segment?

---

## 7. Predictors must pay for themselves

Predictor selection should ultimately follow the same rule.

The predictor with minimum MSE is not necessarily the predictor with the best
rate-distortion cost.

A candidate predictor may:

- reduce residual magnitude;
- change residual sparsity;
- change the best residual codec;
- require different metadata;
- produce a different final byte count.

Future selection should therefore consider the encoded result, not only the
prediction error.

---

## 8. Residual coding must be rate-aware

BANANA-GATE³ showed that ZigZag + varint does not exploit zero-heavy residual
distributions when every value still occupies one byte.

Nitro v2 therefore introduces the design principle of per-block codec
selection.

Candidate representations can include:

```text
raw int32
ZigZag + varint
zero-run + varint
```

The encoder should construct or accurately measure competing representations
and select the one with the lowest actual encoded cost.

A specialized codec must never be selected merely because the data appears
suited to it.

It must produce a smaller representation.

---

## 9. Fallback is a valid coding decision

Locally predictable structure is the specialization of Lasagna 2.

It is not an obligation imposed on every region of every signal.

If a region is poorly predictable and the structural cost of modeling it
exceeds the benefit, the encoder should be able to choose a cheaper fallback
representation.

Conceptually:

```text
MODEL
  if structure pays for itself

FALLBACK
  if modeling costs more than it saves
```

The fallback need not always be raw storage.

It is simply the least expensive valid representation among the available
coding modes for the required quality target.

---

## 10. Nitro v2: first implementation step

The first Nitro iteration does not attempt full global rate-distortion
optimization.

Its purpose is to remove measured structural inefficiencies while preserving
a controlled implementation scope.

The planned first stage includes:

```text
compact segment metadata
per-block residual codec selection
zero-aware residual representation
explicit format version 2
v1/v2 decoder dispatch
pre/post rate-distortion benchmarking
```

This establishes the mechanisms required for later rate-aware decisions.

---

## 11. Beyond Nitro v2

A later encoder may jointly evaluate:

```text
segment boundaries
predictor
quantization
residual codec
fallback representation
```

against a common objective:

```text
J = D + λR
```

Possible search strategies include:

- dynamic programming;
- rate-aware greedy optimization;
- beam search;
- pruning;
- bounded candidate search.

The algorithm is not predetermined.

The invariant is the objective:

> structural complexity must justify its encoded cost.

---

## 12. Research discipline

Lasagna 2 should be evaluated primarily through rate-distortion measurements,
not compression ratio alone.

Relevant metrics include:

```text
encoded bytes
bits per sample
RMSE
maximum absolute error
rate-distortion curves
Pareto frontier
encoding time
decoding time
```

Compression ratio without a corresponding distortion measurement is
insufficient for evaluating a lossy predictive codec.

Performance claims must distinguish:

- synthetic datasets from real datasets;
- lossless baselines from lossy representations;
- measured results from design hypotheses;
- current implementation from planned Nitro behavior.

---

## 13. Design invariant

The governing principle of Lasagna 2 is therefore:

> **Model structure only when structure pays for itself.**

A segment must pay for itself.

A predictor must pay for itself.

A metadata field must pay for itself.

A specialized residual representation must pay for itself.

If a structure does not improve the required rate-distortion objective enough
to justify its encoded cost, it should not enter the bitstream.

That is the transition from the Lasagna MVP to a rate-aware predictive codec.

---

## 14. V2 semantic contract freeze

This section is normative.

The keywords **SHALL** and **SHALL NOT** define requirements that cannot be
changed within format version 2 after its physical wire layout is frozen.

### 14.1 Contract layers

Lasagna 2 SHALL distinguish three independent contracts:

```text
semantic contract
    frozen by M2.2A

numeric representation contract
    characterized by M2.3

wire-layout contract
    selected and frozen by M2.4
```

M2.2A freezes meaning.

M2.3 SHALL characterize candidate numeric representations.

M2.4 SHALL select exactly one physical layout for format version 2.

No encoder SHALL emit a file with `format_version = 2` before M2.3 has
completed and M2.4 has frozen that single physical layout.

### 14.2 Semantic field set and order

A V2 segment SHALL contain the following semantic fields in this order:

```text
1. start_idx
2. end_idx
3. predictor_type
4. mean
5. slope
6. intercept
7. quant_step_Q
8. seed_value
```

This semantic field set and order SHALL NOT change within format version 2.

The physical numeric width of fields 4–8 is intentionally NOT frozen by
M2.2A.

### 14.3 Type categories

The semantic type categories SHALL be:

```text
start_idx       unsigned integer
end_idx         unsigned integer
predictor_type  unsigned integer / closed predictor enum

mean            real-valued signal metadata
slope           real-valued predictor metadata
intercept       real-valued predictor metadata
quant_step_Q    positive real quantization step
seed_value      real-valued signal-domain seed
```

M2.3 SHALL characterize only the physical representation of the five
real-valued metadata fields.

### 14.4 Loss-tolerance categories

The fields SHALL be divided into two loss-tolerance classes.

#### Exact

```text
start_idx
end_idx
predictor_type
```

These fields SHALL round-trip exactly.

V2 SHALL NOT introduce lossy representation of segment boundaries or
predictor identity.

#### Bounded

```text
mean
slope
intercept
quant_step_Q
seed_value
```

These fields MAY use a lossy physical numeric representation only if that
representation satisfies the pre-declared M2.3 acceptance thresholds.

No bounded field representation SHALL be accepted merely because it reduces
the segment-entry size.

### 14.5 Semantic invariants

For every valid non-empty segment:

```text
start_idx <= end_idx
```

Equality is valid and represents a one-sample segment.

The current closed predictor enum SHALL be:

```text
0 = mean
1 = linear
2 = random-walk
```

No other predictor identifier SHALL be interpreted as valid V2 predictor
semantics without a format-contract revision.

`quant_step_Q` SHALL be finite and strictly greater than zero.

The current encoder derives:

```text
Q = max(C_Q * sigma, Q_MIN)
```

with a positive `Q_MIN`.

M2.2A does NOT freeze a universal numeric value of `Q_MIN` into the V2 wire
contract. It freezes only the semantic invariant `Q > 0`.

`seed_value` SHALL represent a value in the numeric domain of the signal.

For the current random-walk predictor, `seed_value` is the first predicted
signal-domain value of the segment.

### 14.6 Predictor-field semantics

The current predictor semantics SHALL be interpreted as:

```text
MEAN
  consumes: mean

LINEAR
  consumes: slope, intercept

RANDOM-WALK
  consumes: seed_value

ALL MODES
  quant_step_Q is residual-quantization metadata
  and SHALL NOT be reinterpreted as a predictor parameter
```

Fields not consumed by a predictor mode MAY remain physically present in the
fixed segment layout, but their presence SHALL NOT change their semantics.

### 14.7 V1 padding status

The three extra V1 `uint32` segment-table slots are formally classified as
non-semantic padding.

For files emitted by the current V1 encoder:

```text
pad1 = 0
pad2 = 0
pad3 = 0
```

The V1 decoder reads these fields and ignores them.

Therefore:

```text
64 B -> 52 B
```

by removing these three fields is lossless by construction with respect to
the current V1 semantic contract.

This 12-byte-per-segment reduction is the only V2 segment-table saving
already guaranteed before M2.3.

### 14.8 Version semantics

The file magic SHALL remain:

```text
LSG2
```

The wire byte order SHALL remain little-endian.

The `format_version` field is a 16-bit unsigned integer in the current file
header.

Its semantics SHALL be:

```text
format_version = 1
    => V1 physical interpretation

format_version = 2
    => exactly one V2 physical interpretation,
       frozen by M2.4

format_version = N
    => exactly one physical interpretation for N
```

One format-version value SHALL NEVER identify multiple incompatible physical
layouts.

No M2.x change SHALL alter the meaning of bytes written with
`format_version = 1`.

V1 is immutable.

After the first valid V2 file is emitted, any incompatible modification to
the V2 physical layout SHALL require a new format-version value.

### 14.9 M2.3 closed candidate-layout set

Before numeric measurements begin, M2.3 SHALL evaluate only the following
pre-registered candidate layouts.

Field order is always:

```text
start_idx
end_idx
predictor_type
mean
slope
intercept
quant_step_Q
seed_value
```

Candidates:

```text
L32
  struct: <IIIfffff
  size:   32 B
  real fields:
    mean=f32
    slope=f32
    intercept=f32
    Q=f32
    seed=f32

L40_PRED64
  struct: <IIIfddff
  size:   40 B
  real fields:
    mean=f32
    slope=f64
    intercept=f64
    Q=f32
    seed=f32

L40_QSEED64
  struct: <IIIfffdd
  size:   40 B
  real fields:
    mean=f32
    slope=f32
    intercept=f32
    Q=f64
    seed=f64

L52
  struct: <IIIddddd
  size:   52 B
  real fields:
    mean=f64
    slope=f64
    intercept=f64
    Q=f64
    seed=f64
```

M2.3 SHALL NOT introduce an additional candidate after observing benchmark
results.

Adding or replacing a candidate SHALL require restarting the M2.3
pre-registration before measurements are considered valid.

`L52` is a reference layout, not a runtime fallback.

M2.4 SHALL select exactly one winning V2 layout.

### 14.10 M2.3 decision discipline

Before running candidate measurements, M2.3 SHALL freeze numeric acceptance
thresholds for the three characterization families:

```text
A. metadata representation error
B. reconstruction delta caused by metadata representation
C. encoded-rate impact caused by metadata representation
```

The thresholds SHALL be declared before results are inspected.

Family A SHALL report at least:

```text
absolute error
relative error where meaningful
normal / subnormal / underflow / overflow behavior
finite-value preservation
```

Family B SHALL relate metadata-induced reconstruction error to the local
quantization step `Q`.

Any chosen bound such as:

```text
|x_candidate - x_f64| <= alpha * Q
```

SHALL state the value of `alpha` and its rationale before measurement.

Family C SHALL report at least:

```text
median rate delta
p95 rate delta
p99 rate delta
maximum per-block rate delta
fraction of blocks whose integer residual changed
fraction of blocks whose varint-length class changed
```

M2.3 SHALL include hostile numeric-scale cases around:

```text
1e-40
1.2e-38
1e-30
1e-12
1
1e6
1e20
```

including the normal/subnormal float32 boundary.

Values outside the declared supported V2 numeric domain SHALL be rejected or
classified explicitly; they SHALL NOT silently define format behavior.

### 14.11 Known V2 representation inefficiencies

The following choices are deliberately retained as non-blocking
inefficiencies for V2:

```text
predictor_type : uint32
start_idx      : absolute uint32
end_idx        : absolute uint32
```

They are retained for simplicity and semantic continuity, not because they
are known to be rate-optimal.

A future format version may evaluate:

```text
predictor_type -> uint8 or varint
start_idx      -> delta from previous segment
end_idx        -> segment length
numeric metadata -> alternate representations such as fixed-point,
                    logarithmic or other bounded encodings
```

Such changes SHALL NOT be introduced into an already-frozen V2 wire layout.

### 14.12 M2.2A invariant

M2.2A SHALL NOT:

```text
change encoder behavior
change decoder behavior
emit V2 bytes
freeze physical widths for bounded real-valued fields
alter V1 semantics
```

Its sole purpose is to freeze the semantic contract against which M2.3 and
M2.4 will be evaluated.

---

## 15. M2.2B-pre — Numeric and corpus pre-registration

This section is normative.

M2.2B-pre freezes the quantitative measurement contract that SHALL govern
M2.3.

No expanded M2.3 corpus SHALL be generated before this section is frozen.

No threshold, measurement level, candidate set, percentile definition,
predictor stratum, or acceptance rule defined here SHALL be changed after
M2.3 measurements begin.

The purpose of this section is pre-registration, not measurement.

### 15.1 Governing methodological rule

> **A benchmark may eliminate candidates; it must never invent the rule that selects them.**

Every hard threshold SHALL have a declared derivation.

A quantity without a derivation SHALL NOT become a hard threshold.

Diagnostic quantities SHALL NOT be promoted to acceptance gates after
results are observed.

### 15.2 Experimental roles

The lossy candidate hypotheses are:

```text
H32
    f32 is sufficient for all five bounded metadata fields
    physical correlate: L32

H_PRED64
    f64 slope/intercept plus f32 mean/Q/seed is sufficient
    physical correlate: L40_PRED64

H_QSEED64
    f64 Q/seed plus f32 mean/slope/intercept is sufficient
    physical correlate: L40_QSEED64
```

`L52` SHALL NOT be treated as a symmetric lossy hypothesis.

`L52` SHALL serve as:

```text
reference representation
reference-path integrity control
conservative selectable layout
```

Its segment metadata representation is:

```text
<IIIddddd
```

with the three non-semantic V1 padding fields removed and all five bounded
real-valued fields retained as float64.

A valid M2.3 experiment SHALL therefore always have `L52` available as its
conservative floor.

### 15.3 Measurement-level principle

A candidate modifies metadata at segment level.

Samples and residual symbols inside the same segment share the same
perturbed metadata and SHALL be treated as clustered observations rather
than independent experimental replicates.

Candidate-discriminating acceptance statistics SHALL therefore be reduced
to exactly one pre-defined statistic per qualifying segment before
cross-segment percentile gates are evaluated.

Sample-level and residual-level observations SHALL be retained only as
within-segment measurements and diagnostics.

### 15.4 Predictor strata

Every qualifying segment SHALL belong to exactly one predictor stratum:

```text
MEAN
    predictor_type = 0

LINEAR
    predictor_type = 1

RW
    predictor_type = 2
```

Acceptance gates SHALL be evaluated independently for every predictor
stratum.

Aggregate results across predictor types SHALL be informational only.

An aggregate result SHALL NOT override, rescue, or invalidate a
stratum-specific result.

An empty or under-covered stratum SHALL be classified as `NOT_EVALUATED`.

`NOT_EVALUATED` SHALL NOT be interpreted as PASS.

### 15.5 Qualifying segment and coverage

A segment SHALL qualify for M2.3 coverage only if:

```text
segment length >= 10 samples
predictor_type is one of MEAN / LINEAR / RW
all reference metadata required by the active predictor are finite
quant_step_Q is finite
quant_step_Q > 0
```

Zero-residual segments SHALL remain valid.

A zero-residual segment SHALL be tagged explicitly and SHALL NOT be removed
from the corpus solely because all quantized residuals are zero.

Hard minimum coverage SHALL be:

```text
MEAN    >= 500 qualifying segments
LINEAR  >= 500 qualifying segments
RW      >= 500 qualifying segments
```

The minimum valid M2.3 corpus therefore contains at least:

```text
1500 qualifying segments
```

The derivation is:

```text
target cross-segment percentile = p99
tail probability                = 0.01

500 segments
    => approximately 5 expected observations beyond p99

100 segments
    => approximately 1 expected observation beyond p99
    => rejected as too fragile for a hard format decision
```

Coverage below 500 qualifying segments in any required predictor stratum
SHALL produce:

```text
M2.3 outcome = INCONCLUSIVE
```

Coverage failure SHALL NOT reject any candidate.

The M1.6 corpus SHALL remain historical sanity evidence.

Repeated evaluation of the same underlying signal with different `C_Q`
values SHALL NOT be counted as independent corpus diversity.

The expanded M2.3 corpus SHALL contain newly generated synthetic signals.

Generator definitions, parameter spaces and case identifiers SHALL be
frozen in the full M2.2B protocol before the first expanded-corpus signal
is generated.

### 15.6 Reproducibility

Synthetic stochastic cases SHALL use deterministic seeds derived from their
canonical case identity.

The canonical identity SHALL have the form:

```text
lasagna2:m2.3:<stratum>:<generator-id>:<case-index>
```

The seed SHALL be derived as:

```text
digest = SHA256(UTF8(case_identity))
seed64 = unsigned-big-endian-integer(digest[0:8])
```

No manually chosen "lucky seed" SHALL be used as the experiment-wide source
of randomness.

Changing a case identity SHALL define a different synthetic case.

### 15.7 Numeric domains D1 / D2 / D3

M2.3 SHALL distinguish three numeric domains.

#### D1 — observed reference domain

`D1` SHALL consist of the bounded metadata values observed in the frozen
pre-M2.3 reference evidence.

D1 SHALL be recorded before expanded-corpus measurement.

D1 SHALL NOT be retroactively widened because of M2.3 results.

#### D2 — supported stress domain

For each bounded real-valued field, let:

```text
m_min = minimum non-zero absolute magnitude observed in D1
m_max = maximum absolute magnitude observed in D1
```

The stress envelope SHALL extend D1 by exactly ten binary exponents:

```text
lower magnitude = m_min / 2^10
upper magnitude = m_max * 2^10
```

where:

```text
2^10 = 1024
```

Signs present in the semantic field SHALL be preserved.

Zero SHALL remain present where zero is semantically valid.

`quant_step_Q = 0` SHALL NOT be introduced because the semantic contract
requires `quant_step_Q > 0`.

D2 SHALL be restricted to finite normal binary32 values.

A D2 value SHALL NOT cross into binary32 subnormal or overflow territory.

The ten-binade expansion is the binary-domain analogue of approximately
three decimal orders of magnitude and is chosen because binary32 precision
and ULP spacing are organized by binary exponent.

#### D3 — boundary characterization domain

D3 SHALL contain binary32 boundary and beyond-boundary cases.

Canonical binary32 boundaries are:

```text
minimum positive subnormal = 2^-149
minimum positive normal    = 2^-126
maximum finite normal      = (2 - 2^-23) * 2^127
```

D3 SHALL include cases around:

```text
normal/subnormal transition
minimum subnormal
underflow below minimum subnormal
upper finite-normal boundary
overflow above maximum finite normal
```

D3 SHALL be informational only.

D3 SHALL NOT reject a candidate.

Subnormal, underflow, overflow, NaN and infinity behavior in D3 SHALL be
tagged explicitly and SHALL NOT be silently coerced.

### 15.8 Canonical percentile definition

Every p99 used by M2.3 SHALL use the same deterministic nearest-rank
definition.

For `N > 0` observations sorted in ascending order:

```text
rank(p) = ceil(p * N)
quantile_p = sorted_values[rank(p) - 1]
```

For p99:

```text
p = 0.99
```

No library-default interpolation rule SHALL replace this definition.

This applies both to within-segment p99 summaries and to cross-segment p99
gates.

### 15.9 Family A — representation-integrity gate

Family A SHALL be an integrity precondition.

Family A SHALL NOT participate in candidate admissibility scoring.

For every field/value pair represented as float32 by a candidate in D1 or
D2, the harness SHALL evaluate:

```text
reference f64
    -> correctly rounded f32
    -> exact f64 widening
```

For finite normal binary32 target values:

```text
ULP distance SHALL be <= 0.5 binary32 ULP
```

The widening step from binary32 to binary64 SHALL be exact.

Absolute representation error SHALL be recorded as a diagnostic.

No independent absolute-error acceptance threshold SHALL be introduced.

The same field/value pair represented as float32 in more than one candidate
SHALL produce exactly the same A result.

Therefore:

```text
A_mean_f32
A_slope_f32
A_intercept_f32
A_Q_f32
A_seed_f32
```

are primitive representation checks whose result is candidate-independent.

A candidate-specific disagreement for the same field/value pair SHALL
produce:

```text
HARNESS_INVALID
```

If a finite D1/D2 source value expected to remain inside the declared
binary32 normal domain produces NaN or infinity through the candidate
conversion path, M2.3 SHALL produce:

```text
HARNESS_INVALID
```

### 15.10 L52 reference-path integrity

For L52, all five bounded metadata fields SHALL remain binary64.

The L52 metadata serialization/deserialization path SHALL preserve each
finite reference binary64 value exactly.

Unexpected numeric change on the L52 reference path SHALL produce:

```text
HARNESS_INVALID
```

L52 reference failure SHALL NOT be classified as ordinary candidate
rejection.

### 15.11 Family B — reconstruction-distortion gate

Family B SHALL measure candidate-induced reconstruction change relative to
L52.

For each qualifying segment `s`, let:

```text
Q_ref(s) = quant_step_Q from the L52/reference metadata
```

For every sample `i` inside the segment:

```text
delta_x(i,s,c) =
    abs(
        x_hat_candidate(i,s,c)
        -
        x_hat_L52(i,s)
    )
    /
    Q_ref(s)
```

For candidate `c`, the segment-level statistic SHALL be:

```text
B_s(c) = p99 over samples i of delta_x(i,s,c)
```

using the canonical nearest-rank p99 definition.

For each predictor stratum, candidate `c` SHALL pass Family B iff:

```text
p99 over qualifying segments s of B_s(c) <= 1/4
```

The `1/4` bound is derived from the quantization scale.

A conventional nearest-step quantizer has a characteristic reconstruction
error scale of approximately `Q/2`.

The metadata-induced reconstruction shift SHALL therefore remain no larger
than half of that characteristic quantization-error scale at the p99 gate:

```text
(Q/2) / 2 = Q/4
```

Family B SHALL be evaluated independently for MEAN, LINEAR and RW.

A candidate failing Family B in any covered predictor stratum SHALL be
inadmissible.

The following SHALL be diagnostics only:

```text
maximum normalized reconstruction delta
within-segment delta spread
max / p99 relationship
```

For RW, the harness SHALL additionally report:

```text
first-sample delta
last-sample delta
maximum delta
within-segment p99 delta
```

These RW diagnostics SHALL distinguish initial seed perturbation from
persistent or growing reconstruction effects.

### 15.12 Family C — rate-economics gate

Family C SHALL measure whether residual perturbation consumes the structural
metadata saving obtained by a lossy candidate.

The L52 segment-entry size is:

```text
52 bytes
```

Candidate metadata savings relative to L52 are therefore:

```text
L32
    52 - 32 = 20 bytes per segment

L40_PRED64
    52 - 40 = 12 bytes per segment

L40_QSEED64
    52 - 40 = 12 bytes per segment
```

Family C SHALL use the existing ZigZag + varint residual representation.

Nitro zero-run coding SHALL NOT participate in M2.3 metadata-precision
characterization.

For each qualifying segment `s` and lossy candidate `c`, define:

```text
residual_penalty(s,c) =
    residual_payload_bytes_candidate(s,c)
    -
    residual_payload_bytes_L52(s)
```

and:

```text
C_s(c) =
    max(0, residual_penalty(s,c))
    /
    metadata_saving(c)
```

Interpretation:

```text
C_s = 0
    no additional residual-payload cost

0 < C_s < 1
    part of the metadata saving is consumed

C_s = 1
    residual cost exactly consumes the metadata saving

C_s > 1
    residual cost exceeds the metadata saving
```

For each predictor stratum, candidate `c` SHALL pass Family C iff:

```text
p99 over qualifying segments s of C_s(c) <= 1
```

The threshold `1` is the exact structural break-even point.

It is therefore derived from encoded-byte economics rather than from an
externally chosen percentage.

A candidate failing Family C in any covered predictor stratum SHALL be
inadmissible.

The following SHALL be diagnostics only:

```text
maximum residual byte penalty
maximum C_s
fraction of quantized residual values that changed
fraction of varint-length classes that changed
fraction of varint-length classes that grew
fraction of varint-length classes that shrank
net residual-byte effect
```

### 15.13 Candidate admissibility

Family A SHALL NOT be part of candidate admissibility.

Family A and the L52 reference path SHALL be measurement-integrity
preconditions.

A lossy candidate SHALL be admissible iff:

```text
Family B passes in MEAN
AND Family B passes in LINEAR
AND Family B passes in RW
AND Family C passes in MEAN
AND Family C passes in LINEAR
AND Family C passes in RW
```

This definition applies only after the coverage gate and all integrity gates
have passed.

### 15.14 ICC diagnostic contract

`ICC_shift` SHALL be diagnostic only.

It SHALL NOT participate in:

```text
candidate admissibility
candidate selection
tie-breaking
```

`ICC_shift` SHALL use a one-way random-effects ICC interpretation with
segments as clusters and normalized sample-level reconstruction deltas as
repeated observations inside each segment.

Interpretation SHALL be restricted to:

```text
high ICC_shift
    strong between-segment component
    metadata perturbation effects differ systematically across segments

low ICC_shift
    within-segment variability dominates total variability
    cause is NOT identified by ICC alone
```

A low ICC_shift SHALL NOT by itself be attributed to quantization noise.

Possible contributors include:

```text
quantization
within-segment signal heterogeneity
local non-stationarity
predictor error inside the segment
residual x quantizer interaction
harness artifacts
```

`ICC_rate` SHALL be classified as:

```text
NOT DEFINED
```

under the current one-residual-block-per-segment format because there is no
within-segment block replication from which to estimate a rate ICC.

The harness SHALL NOT fabricate `ICC_rate` from bytes or residual symbols
solely to produce an ICC value.

### 15.15 Total M2.3 outcome model

M2.3 SHALL have exactly the following top-level outcome classes.

```text
INCONCLUSIVE

HARNESS_INVALID

WINNER
```

`INCONCLUSIVE` SHALL mean that required experimental coverage is missing.

`HARNESS_INVALID` SHALL mean that measurement integrity is broken,
including at least:

```text
L52 reference-path failure
Family A inconsistency
unexpected NaN/Inf in the declared D1/D2 normal-f32 domain
other violated frozen harness invariants
```

A valid and sufficiently covered M2.3 experiment SHALL always produce a
winner because L52 is the conservative reference/control layout.

`NO-WINNER` SHALL NOT be a valid M2.3 outcome.

The winner SHALL be exactly one of:

```text
L32
L40_PRED64
L40_QSEED64
L52
```

If every lossy candidate fails Family B or Family C, the valid scientific
result SHALL be:

```text
WINNER = L52
```

which means:

```text
the 12-byte V1 padding removal remains validated
the additional 20-byte f64-to-f32 opportunity is not justified
under the frozen numeric contract and study domain
```

### 15.16 Corpus-generation barrier

M2.2B-pre freezes quantitative rules but SHALL NOT itself authorize expanded
corpus generation.

The full M2.2B protocol SHALL freeze, before generation begins:

```text
synthetic generator definitions
generator parameter spaces
canonical generator identifiers
case-index ranges
predictor-stratum construction rules
corpus manifest format
candidate-selection procedure
tie-break procedure
```

No expanded-corpus sample SHALL be generated before that full protocol
freeze.

Therefore the required order SHALL remain:

```text
M2.2A
    semantic contract freeze

M2.2B-pre
    numeric + corpus pre-registration

M2.2B
    complete methodology + generator + selection freeze

corpus generation
    only after M2.2B PASS

M2.3
    measurement only

M2.4
    freeze exactly one physical V2 wire layout
```

---

## 16. M2.2B — Executable methodology freeze

This section is normative.

M2.2B converts the semantic and quantitative contracts frozen in M2.2A
and M2.2B-pre into a fully executable experimental method.

M2.2B SHALL freeze the method only.

It SHALL NOT generate, materialize, inspect, score, reject, replace or
select any M2.3 synthetic corpus case.

```text
CORPUS_GENERATION_AUTHORIZED = NO
```

M2.2C SHALL be the only phase authorized to materialize the frozen M2.3 corpus.

### 16.1 Provenance classification

The M2.2B.0 read-only provenance audit established:

```text
PROVENANCE_WORLD = B
```

The historical M1 files exist and are versioned, but the generator that
created those historical `data/examples` files is not recoverable from the
repository history.

The current `tools/generate_demo_data.py` was introduced after the
historical example datasets and produces `data/demo`, not the historical
`data/examples` inputs.

Therefore:

```text
M1.6 = historical sanity evidence
M2.3 corpus = new reproducible experimental corpus
```

M1.6 SHALL NOT contribute to M2.3 coverage.

The M2.3 corpus SHALL NOT be described as:

```text
a regenerated M1.6 corpus
a genetic expansion of M1.6
the original M1 generator output
```

No KS test or other distributional test SHALL be used to manufacture a
genetic-equivalence claim between M1.6 and the new M2.3 corpus.

Any comparison between M1.6 and M2.3 distributions SHALL be diagnostic
only.

### 16.2 Contract anchor architecture

The canonical anchor manifest SHALL be normative.

Its path SHALL be:

```text
docs/m2-2b-anchors.tsv
```

The expected manifest hash is:

```text
EXPECTED_M2_2B_ANCHOR_MANIFEST_SHA256 = 7abc9619f1ac7b8fde46fd4db08d665d6e97dddc5fd92493b94a6cdb73e33364
```

The contract SHALL consist of the versioned pair:

```text
docs/rate-distortion-design.md
docs/m2-2b-anchors.tsv
```

The verifier SHALL:

```text
1. read the expected manifest SHA256 from this document
2. hash the manifest bytes
3. require exact SHA256 equality
4. read canonical phrases from the manifest
5. require each phrase verbatim in this document
6. require exactly one occurrence of every canonical phrase
```

The verifier SHALL NOT contain an independent canonical phrase list.

The manifest SHALL NOT be patched merely to make a verifier failure pass.

After freeze:

```text
manifest hash mismatch
    -> HARNESS_INVALID

manifest malformed
    -> HARNESS_INVALID

manifest anchor absent verbatim from document
    -> CONTRACT_INCOMPLETE

manifest anchor duplicated in document
    -> CONTRACT_INCOMPLETE

manifest + document valid but verifier reports otherwise
    -> HARNESS_INVALID
```

Paraphrase SHALL NOT count as canonical-anchor presence.

### 16.3 Reference encoder identity

The reference encoder SHALL be the current V1 encoder implementation whose
source file is:

```text
lasagna2/core.py
```

with:

```text
REFERENCE_CORE_SHA256 = a29c3dd384812061b24652a74f2c89236ed7e9bf4803fc2b2512f9c367da1701
```

The reference configuration SHALL be exactly:

```text
format_version       = 1
segment_mode         = adaptive
predictor            = auto
C_Q                  = 0.5
Q_MIN                = 1e-6
min_segment_length   = 32
max_segment_length   = 128
mse_threshold        = 0.5
residual_coding      = varint
```

`segment_length` is irrelevant under adaptive segmentation and SHALL NOT
be interpreted as a corpus parameter.

The reference encoder SHALL NOT use randomness.

M2.2C SHALL encode every generated input twice with this frozen reference
configuration.

The two byte streams SHALL be identical.

A mismatch SHALL produce:

```text
HARNESS_INVALID
```

### 16.4 Historical D1 source and deterministic D2 derivation

D1 SHALL be derived only from these historical fixed inputs:

```text
data/examples/trend.csv
SHA256 = 1cb13a9c80b2a9944b1eb13c18472972e695895b409bb217171f56166d420746

data/examples/sine_noise.csv
SHA256 = e555b47912504c4405806c97f6d50ff408ef9201e0ef1904de7704ccecb4362e

data/examples/flat_spike.csv
SHA256 = 9a429b08d1abb3f2b53afde333248fb0ad7b2685f44608633c4b666b1b8c39be
```

Historical CSV loading for D1 SHALL follow the frozen M1 parser semantics:

```text
read UTF-8 lines
strip whitespace
skip blank lines
skip lines beginning with '#'
take the first comma-separated token
attempt binary64 conversion
ignore lines whose first token is not numeric
```

Each historical series SHALL then be encoded with the frozen V1 reference
configuration.

The active bounded metadata emitted by that reference encode SHALL define
D1.

D2 SHALL then be derived exactly as frozen in M2.2B-pre:

```text
non-zero D1 minimum magnitude / 2^10
through
D1 maximum magnitude * 2^10
```

restricted to finite normal binary32.

If a field contains no non-zero D1 observation, its non-zero D2 extension
SHALL be empty; zero remains valid only where permitted by the semantic
contract.

D1/D2 derivation SHALL occur in M2.2C before any expanded-corpus case is
generated.

### 16.5 Predictor stratum assignment

M2.2B SHALL NOT infer strata from generator names.

The generator label expresses construction intent only.

The normative assignment is:

```text
stratum(segment) = predictor_type stored by the frozen V1 reference encode
```

with:

```text
0 -> MEAN
1 -> LINEAR
2 -> RW
```

No candidate layout SHALL reassign a segment to another stratum.

No post-hoc semantic classifier SHALL override the reference wire.

### 16.6 Qualifying-segment predicate

The predicate SHALL be evaluated only on the frozen V1 reference segment.

```text
qualifying(reference_segment) SHALL be candidate-independent.
```

Checks SHALL occur in this order:

```text
1. length >= 10

2. predictor_type in {0, 1, 2}

3. determine active bounded metadata from predictor_type

4. all active bounded metadata are finite

5. Q_ref is finite and Q_ref > 0

6. all active bounded metadata belong to D1 union D2
```

Active bounded metadata SHALL be:

```text
MEAN:
    mean
    Q

LINEAR:
    slope
    intercept
    Q

RW:
    seed
    Q
```

Inactive metadata SHALL NOT disqualify a segment.

Therefore:

```text
LINEAR with slope = 0
    -> may qualify

zero-residual segment
    -> may qualify
    -> SHALL be tagged

reference active metadata in D3
    -> NOT qualifying
    -> informational only
```

If a qualifying reference segment causes a lossy candidate conversion to
produce NaN or infinity, that segment SHALL NOT disappear from coverage.

The result SHALL instead follow the Family-A integrity rules.

### 16.7 Coverage contract

```text
M2.2B-COVERAGE: each of MEAN, LINEAR and RW SHALL contain at least 500 qualifying reference segments.
```

Coverage SHALL be computed after the full frozen case set has been generated
exactly once and reference-encoded.

Coverage SHALL NOT be reached by:

```text
changing a seed
retrying a case
discarding an inconvenient case
adding extra cases
extending the case-index range
changing generator parameters
```

Seed-shopping SHALL be prohibited.

If any required stratum has fewer than 500 qualifying reference segments:

```text
M2.2C = INCONCLUSIVE
```

The same frozen M2.2B protocol SHALL NOT be extended opportunistically.

Any larger corpus SHALL require an explicit new protocol revision and a new
freeze before generation.

### 16.8 Case grid

M2.3 corpus v1 SHALL contain exactly three generator families:

```text
GENERATOR = mean_stationary_v1
GENERATOR = linear_trend_v1
GENERATOR = random_walk_v1
```

For each generator:

```text
binade index:
    b in [-10, -9, ..., 0, ..., +9, +10]
    21 values

stochastic level:
    l in [0, 1, 2, 3, 4]
    5 values

replicate:
    r in [0, 1, 2, 3, 4]
    5 values
```

Therefore:

```text
21 * 5 * 5 = 525 cases per generator
525 * 3     = 1575 total cases
```

Every case SHALL contain:

```text
CASE_LENGTH = 512
```

samples.

The 21-binade axis SHALL be an absolute signal-scale axis:

```text
scale(b) = 2^b
```

It SHALL NOT be an SNR axis.

The five stochastic levels SHALL use:

```text
rho(l) = 2^(l - 6)

l=0 -> 1/64
l=1 -> 1/32
l=2 -> 1/16
l=3 -> 1/8
l=4 -> 1/4
```

At fixed `l`, multiplying the signal by `scale(b)` SHALL scale deterministic
and stochastic components together.

Therefore the dimensionless stochastic ratio remains fixed across binades.

The five stochastic levels are corpus-design coordinates, not acceptance
thresholds.

### 16.9 Case identity and seed derivation

Canonical case identity SHALL be:

```text
lasagna2:m2.3:v1:<generator_id>:b=<B>:l=<L>:r=<R>
```

where:

```text
<B> = signed decimal binade with explicit sign and width 3
      examples: -10, -01, +00, +01, +10

<L> = decimal digit 0..4

<R> = decimal digit 0..4
```

Example:

```text
lasagna2:m2.3:v1:random_walk_v1:b=-03:l=2:r=4
```

The seed SHALL be:

```text
digest = SHA256(UTF8(case_id))
seed64 = unsigned big-endian integer represented by digest[0:8]
```

The mapping SHALL be a pure function of case identity.

It SHALL be independent of:

```text
generation order
filesystem order
manifest order
previous PRNG state
parallel execution order
```

### 16.10 PRNG

```text
PRNG = SplitMix64
```

Each case SHALL create a fresh SplitMix64 state initialized with `seed64`.

All SplitMix64 arithmetic SHALL use unsigned 64-bit arithmetic modulo
`2^64`.

One output SHALL be generated as:

```text
state = state + 0x9E3779B97F4A7C15  mod 2^64
z = state
z = (z xor (z >> 30)) * 0xBF58476D1CE4E5B9  mod 2^64
z = (z xor (z >> 27)) * 0x94D049BB133111EB  mod 2^64
z = z xor (z >> 31)
output = z
```

A binary64 uniform value in `[0, 1)` SHALL be:

```text
u01 = (output >> 11) * 2^-53
```

A binary64 symmetric uniform value in `[-1, +1)` SHALL be:

```text
u = 2*u01 - 1
```

No host-language random module SHALL participate in M2.3 corpus generation.

### 16.11 Numeric execution model

Generator arithmetic SHALL use IEEE-754 binary64 round-to-nearest,
ties-to-even.

Intermediate generator values SHALL remain binary64.

No fused multiply-add SHALL be assumed by the normative formulas.

The canonical input payload SHALL be the final sequence packed as contiguous
little-endian binary64 values:

```text
<Nd
```

with `N = 512`.

### 16.12 Generator formulas

For every case define:

```text
N   = 512
s   = 2^b
rho = 2^(l - 6)
u_i = successive SplitMix64 symmetric-uniform draws
```

#### mean_stationary_v1

For:

```text
i = 0 .. N-1
```

generate:

```text
x_i = s * (1 + rho * u_i)
```

This generator is designed to provide stationary local structure.

It SHALL NOT determine the final predictor stratum.

#### linear_trend_v1

For:

```text
t_i = i / (N - 1)
```

generate:

```text
x_i = s * (1 + t_i + rho * u_i)
```

This generator is designed to provide linear local structure across the
full case.

It SHALL NOT determine the final predictor stratum.

#### random_walk_v1

Generate the first sample as:

```text
x_0 = s * (1 + rho * u_0)
```

Then for:

```text
i = 1 .. N-1
```

generate:

```text
x_i = x_(i-1) + s * rho * u_i
```

This generator exists specifically to provide a construction capable of
exercising the RW predictor and `seed_value`.

It SHALL NOT force RW classification.

Only the frozen V1 reference wire determines the resulting stratum.

### 16.13 Noise-model scope

The M2.3 v1 stochastic model SHALL be bounded uniform noise/innovation
derived directly from SplitMix64.

It SHALL NOT use Gaussian noise.

This choice removes dependence on transcendental Gaussian transforms and
makes exact case reproduction simpler across independent implementations.

The uniform model has compact support and therefore differs statistically
from Gaussian historical examples.

This distinction SHALL be reported.

The Family-B `Q/4` threshold and Family-C break-even threshold SHALL NOT be
described as calibrated to the uniform distribution.

Their derivations are independent of this corpus noise distribution:

```text
B:
    derived from quantization scale Q

C:
    derived from encoded-byte break-even
```

Changing the noise model SHALL define a new corpus protocol revision.

It SHALL NOT retroactively alter the derivation of B or C.

### 16.14 Segment-opportunity rationale

The reference configuration has:

```text
max_segment_length = 128
```

and every corpus case has:

```text
512 samples
```

Therefore every fully consumed case has at least four reference segment
opportunities before qualification and stratum filtering.

Per generator family:

```text
525 cases * at least 4 reference segments
    >= 2100 reference segment opportunities
```

This is deliberate over-provisioning relative to the 500-segment hard
coverage requirement.

It SHALL NOT be interpreted as a guarantee of 500 segments in the intended
stratum.

Only M2.2C reference-wire counts determine actual coverage.

### 16.15 Corpus materialization interface

M2.2C SHALL materialize corpus v1 under:

```text
data/m2-3/
```

with:

```text
data/m2-3/cases/
data/m2-3/reference/
data/m2-3/manifest.tsv
data/m2-3/reference-segments.tsv
```

Input case payloads SHALL be raw contiguous little-endian binary64 values
with no header.

The relative input path SHALL be:

```text
cases/<generator_id>/b<B>/l<L>/r<R>.f64le
```

using the same canonical `<B>`, `<L>`, `<R>` formatting as the case ID.

Reference V1 files SHALL use:

```text
reference/<generator_id>/b<B>/l<L>/r<R>.lsg2
```

### 16.16 Corpus manifest schema

`data/m2-3/manifest.tsv` SHALL be UTF-8 with LF line endings.

Rows SHALL be ordered lexicographically by `case_id`.

Its exact columns SHALL be:

```text
case_id
generator_id
binade
level
replicate
seed64_hex
n_samples
input_relpath
input_sha256
reference_relpath
reference_sha256
reference_segment_count
qualifying_segment_count
```

`seed64_hex` SHALL be lowercase hexadecimal with exactly 16 digits.

SHA256 values SHALL be lowercase hexadecimal with exactly 64 digits.

No field SHALL depend on directory enumeration order.

### 16.17 Reference-segment manifest

`data/m2-3/reference-segments.tsv` SHALL be UTF-8 with LF line endings.

Rows SHALL be ordered by:

```text
case_id ascending
segment_id ascending
```

Its exact columns SHALL be:

```text
case_id
segment_id
start_idx
end_idx
length
predictor_type
stratum
mean
slope
intercept
Q
seed
zero_residual
qualifying
```

Binary64 metadata values SHALL be serialized textually using Python-style
hexadecimal floating-point notation equivalent to `float.hex()`.

This avoids decimal formatting ambiguity.

Boolean fields SHALL be serialized exactly as:

```text
0
1
```

### 16.18 Reference corpus determinism gates

For every case, M2.2C SHALL verify:

```text
generated input SHA256 is deterministic from case_id
reference encode #1 == reference encode #2 byte-for-byte
reference segment extraction is deterministic
manifest ordering is canonical
```

Failure of any of these SHALL produce:

```text
HARNESS_INVALID
```

M2.2C SHALL NOT repair such a failure by changing a seed.

### 16.19 M2.3 candidate comparison set

The reference segmentation SHALL be frozen from the V1 reference encode.

Candidate metadata precision SHALL NOT alter:

```text
segment boundaries
reference predictor_type
stratum assignment
coverage denominator
case membership
```

The selectable layouts SHALL be:

```text
L32
L40_PRED64
L40_QSEED64
L52
```

L52 SHALL remain the exact numeric reference/control.

Lossy candidate admissibility SHALL be determined exclusively by the frozen
Family B and Family C rules.

### 16.20 Measured-rate selection

Candidate selection SHALL use measured comparable encoded rate, not nominal segment-entry size.

For candidate `c` and predictor stratum `k`, define:

```text
comparable_bytes(c,k) =
    sum over qualifying segments in k of:
        segment_entry_bytes(c)
      + residual_block_header_bytes
      + actual residual_payload_bytes(c)
```

Global file/header/context bytes that are identical across all layouts SHALL
be omitted from comparison.

Define:

```text
R_k(c) =
    8 * comparable_bytes(c,k)
    /
    total_reference_samples_in_qualifying_segments(k)
```

in bits per sample.

The primary selection score SHALL be:

```text
R_select(c) =
    (R_MEAN(c) + R_LINEAR(c) + R_RW(c)) / 3
```

Each predictor stratum therefore has equal weight regardless of how many
additional qualifying segments it contains above the 500-segment floor.

The candidate pool SHALL contain:

```text
L52
plus every lossy candidate admissible under B and C
```

The smallest `R_select` SHALL win unless an exact tie requires the frozen
tie-break procedure.

### 16.21 Numeric tie-break hierarchy

If two or more candidate layouts have exactly equal `R_select`, compare,
in this order, lower being preferred:

```text
1. worst-stratum p99 normalized reconstruction delta

2. worst-stratum maximum normalized reconstruction delta

3. worst-stratum p99 C_s rate-economics statistic

4. worst-stratum maximum C_s

5. worst-stratum fraction of changed quantized residuals

6. worst-stratum fraction of changed varint-length classes
```

For each metric:

```text
worst-stratum = max(MEAN, LINEAR, RW)
```

If candidates remain identical after all six numeric levels:

```text
FINAL_CANONICAL_TIE_BREAK = L52 > L40_PRED64 > L40_QSEED64 > L32
```

This final ordering SHALL apply only after measured encoded rate and all
preceding numeric tie-break metrics are equal.

Its meaning is conservative:

```text
when measured cost and measured behavior are indistinguishable,
retain the greater numeric precision
```

It SHALL NOT override a measurable rate advantage.

### 16.22 ICC status

`ICC_shift` remains diagnostic exactly as frozen in M2.2B-pre.

```text
M2.2B-ICC-RATE: ICC_rate remains NOT DEFINED.
```

No rate ICC SHALL be fabricated from residual symbols.

### 16.23 Total outcome function

After M2.2C corpus construction and M2.3 measurement:

```text
insufficient qualifying coverage
    -> INCONCLUSIVE

reference/verifier/integrity failure
    -> HARNESS_INVALID

otherwise
    -> exactly one WINNER
```

The winner SHALL be:

```text
L32
L40_PRED64
L40_QSEED64
or L52
```

If no lossy candidate is admissible:

```text
WINNER = L52
```

If lossy candidates are admissible but none beats L52 on measured encoded
rate and tie-break rules:

```text
WINNER = L52
```

Therefore `NO-WINNER` remains unreachable in a valid, sufficiently covered
M2.3 experiment.

### 16.24 Freeze barrier

M2.2B freezes:

```text
provenance interpretation
anchor manifest architecture
verifier behavior
reference encoder identity
D1 source
D2 derivation
qualifying predicate
stratum assignment
coverage rule
case grid
case identity
seed mapping
PRNG
uniform mapping
generator formulas
noise model
case length
corpus binary representation
manifest schemas
selection metric
tie-break hierarchy
outcome function
```

M2.2B SHALL NOT generate the expanded corpus.

The next phases SHALL remain:

```text
M2.2C
    generate and materialize exactly the frozen corpus
    verify reproducibility
    verify coverage

M2.3
    measurements only

M2.4
    freeze the unique winning physical V2 layout
```

Each freeze stage may discover methodological constraints for later stages,
but SHALL NOT retroactively reinterpret evidence already frozen by an
earlier stage.

### 16.25 Protocol revision 1.1 — Reference TimeSeries context

This amendment was frozen before any M2.2C corpus generation or
materialization.

Its sole purpose is to remove an execution-level ambiguity in the V1
reference byte stream.

```text
PROTOCOL_REVISION = 1.1
```

The reference `TimeSeries` context SHALL be exactly:

```text
REFERENCE_TIMESERIES_CONTEXT = dt=1.0; t0=1970-01-01T00:00:00Z; unit=benchmark
```

These values are inherited from the already established M1 benchmark
interface.

They do not alter:

```text
sample values
segment boundaries
predictor selection
quantization
qualification
stratum assignment
Family B
Family C
```

They do affect the serialized V1 context JSON and therefore SHALL be frozen
before reference `.lsg2` byte identity and SHA256 values are measured.

No other M2.2B rule is changed by protocol revision 1.1.

