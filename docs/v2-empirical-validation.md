# V2 Empirical Validation — Canonical Corpus V1 vs V2

## Status

**Evidence type:** observational / empirical validation

**Protocol revision:** 2.1

**Protocol mutation:** NO

**M2.3 selection reopened:** NO

**M2.4 physical freeze reopened:** NO

**Repository state evaluated:**

```text
5d6b65a69c30178741b5d0d2e3348a99d5443662
```

This document records the empirical result obtained after completing the V2
selection, physical freeze, wire implementation, and public interface.

It does not redefine the selection methodology, numerical acceptance
thresholds, wire contract, or physical layout.

---

## 1. Validation chain

The empirical validation follows the already completed sequence:

```text
M2.3 candidate selection
        ↓
L32 selected
        ↓
M2.4 physical freeze
        ↓
<IIIfffff>, 32-byte segment entry
        ↓
V2 wire implementation
        ↓
public Python API + CLI
        ↓
canonical-corpus empirical validation
```

Relevant commits:

```text
M2.3 selection evidence
821c50cf17778f5951505bcf1895b75a45a3ff88

M2.4 L32 physical freeze
61ae6cedd094d3272274f17d0d5e5f5c8476cea8

V2 wire implementation
40158d3f1bb83065b5150328248aa3cc812f98e2

V2 public interface
5d6b65a69c30178741b5d0d2e3348a99d5443662
```

The selection decision was not reopened during this validation.

---

## 2. Frozen identities

Protocol contract:

```text
PROTOCOL_REVISION=2.1

PROTOCOL_ANCHOR_MANIFEST_SHA256
5a197e5c0eed2d333cf3dc8be18c6b000cb0550c75491f4389152c15886a4b5a
```

Canonical corpus:

```text
CORPUS_MANIFEST_SHA256
20e69077397efe73815d5c594d1ef94281f7777d9bd8c861c0db34a9e55f03dc

REFERENCE_SEGMENTS_SHA256
ae4d9cd6e48640d29ac856333b7d47d2da5714abdced3ae1b2d476877a05ba8a
```

Corpus cardinality:

```text
cases     = 1575
samples   = 806400
segments  = 11700
```

Predictor strata are balanced:

```text
MEAN    525 cases | 268800 samples | 3900 segments
LINEAR  525 cases | 268800 samples | 3900 segments
RW      525 cases | 268800 samples | 3900 segments
```

---

## 3. Integrity and determinism

The canonical V1 streams were regenerated from the canonical input cases and
compared byte-for-byte with every tracked V1 reference file.

Result:

```text
V1_BYTE_IDENTITY=1575/1575
```

V2 was encoded twice independently for every canonical case.

Result:

```text
V2_DOUBLE_ENCODE_IDENTITY=1575/1575
```

Therefore:

```text
V1_REFERENCE_INTEGRITY_GATE=PASS
V2_DETERMINISM_GATE=PASS
```

---

## 4. Canonical V1 size baseline

The correct baseline for comparing physical file size is the sum of the 1575
canonical reference `.lsg2` files named by the corpus manifest.

```text
CANONICAL_REFERENCE_FILE_BYTES=1875150
```

An earlier experimental harness reported:

```text
LEGACY_REFERENCE_STREAM_BYTES=1958104
```

The difference is:

```text
82954 bytes
```

The historical value is retained as provenance but is not used as the
canonical file-size baseline.

The canonical physical-size baseline is derived directly from the tracked
reference files.

---

## 5. Overall V1 vs V2 size result

```text
V1_TOTAL_BYTES=1875150
V2_TOTAL_BYTES=1500750

BYTES_SAVED=374400
PERCENT_SAVED=19.966402688
```

Rate per input sample:

```text
V1_BITS_PER_SAMPLE=18.602678571
V2_BITS_PER_SAMPLE=14.888392857

BITS_PER_SAMPLE_SAVED=3.714285714
```

Thus the frozen V2 physical representation reduces the canonical corpus wire
size by approximately **19.97%** relative to V1.

---

## 6. Structural accounting

V1 segment entry:

```text
<6Iddddd>
64 bytes
```

Frozen V2 L32 segment entry:

```text
<IIIfffff>
32 bytes
```

Across 11700 canonical segments:

```text
V1_SEGMENT_TABLE_BYTES=748800
V2_SEGMENT_TABLE_BYTES=374400

METADATA_THEORETICAL_SAVING_BYTES=374400
ACTUAL_SEGMENT_TABLE_SAVING_BYTES=374400
```

Residual payload:

```text
V1_RESIDUAL_PAYLOAD_BYTES=806400
V2_RESIDUAL_PAYLOAD_BYTES=806400

RESIDUAL_PAYLOAD_DELTA_BYTES=0
```

Other non-segment wire content:

```text
FIXED_NONSEGMENT_DELTA_BYTES=0
```

Net effect outside the segment table:

```text
NONMETADATA_NET_EFFECT_BYTES=0
NONMETADATA_NET_EFFECT=BYTE_NEUTRAL
```

Therefore the complete observed wire-size improvement is accounted for exactly
by the reduction of the segment entry from 64 bytes to 32 bytes.

No byte saving was lost to a larger residual payload, and no additional byte
saving was obtained elsewhere.

---

## 7. Result by predictor

### MEAN

```text
CASES=525
SAMPLES=268800
SEGMENTS=3900

V1_BYTES=625050
V2_BYTES=500250

BYTES_SAVED=124800
PERCENT_SAVED=19.966402688

V1_BPS=18.602678571
V2_BPS=14.888392857

SEGMENT_TABLE_SAVING_BYTES=124800

V1_RESIDUAL_PAYLOAD_BYTES=268800
V2_RESIDUAL_PAYLOAD_BYTES=268800
RESIDUAL_PAYLOAD_DELTA_BYTES=0

NONMETADATA_NET_EFFECT_BYTES=0
```

### LINEAR

```text
CASES=525
SAMPLES=268800
SEGMENTS=3900

V1_BYTES=625050
V2_BYTES=500250

BYTES_SAVED=124800
PERCENT_SAVED=19.966402688

V1_BPS=18.602678571
V2_BPS=14.888392857

SEGMENT_TABLE_SAVING_BYTES=124800

V1_RESIDUAL_PAYLOAD_BYTES=268800
V2_RESIDUAL_PAYLOAD_BYTES=268800
RESIDUAL_PAYLOAD_DELTA_BYTES=0

NONMETADATA_NET_EFFECT_BYTES=0
```

### RANDOM WALK

```text
CASES=525
SAMPLES=268800
SEGMENTS=3900

V1_BYTES=625050
V2_BYTES=500250

BYTES_SAVED=124800
PERCENT_SAVED=19.966402688

V1_BPS=18.602678571
V2_BPS=14.888392857

SEGMENT_TABLE_SAVING_BYTES=124800

V1_RESIDUAL_PAYLOAD_BYTES=268800
V2_RESIDUAL_PAYLOAD_BYTES=268800
RESIDUAL_PAYLOAD_DELTA_BYTES=0

NONMETADATA_NET_EFFECT_BYTES=0
```

All three predictor strata exhibit the same physical-size reduction because
the corpus contains the same number of segments in each stratum and the
residual payload remains byte-neutral.

---

## 8. Distortion — overall

Measured against the original binary64 input samples:

```text
V1_MSE=42.510900148038552
V2_MSE=42.510899806148366

V1_RMSE=6.5200383547981184
V2_RMSE=6.5200383285796999
```

Relative MSE:

```text
V2_OVER_V1_MSE_RATIO=0.99999999195758771
V2_MSE_CHANGE_PERCENT=-8.04241229169e-07
```

Direct reconstruction difference between V2 and V1:

```text
V2_VS_V1_RECON_RMSE=0.0020690522129429836
```

Maximum absolute reconstruction errors against the original signal:

```text
V1_MAX_ABS_ERROR=404.78551872349408
V2_MAX_ABS_ERROR=404.78565010548255
```

Largest observed pointwise difference between the two reconstructed streams:

```text
V2_VS_V1_MAX_ABS_DIFF=1.8358195631620902
```

The tiny aggregate MSE decrease observed for V2 is not interpreted as evidence
that binary32 metadata is intrinsically more accurate. It is an incidental
effect of numerical perturbation and rounding.

The relevant empirical result is that the aggregate distortion remains
effectively unchanged at corpus scale while the physical wire size decreases.

---

## 9. Distortion by predictor

### MEAN

```text
V1_RMSE=2.7300312009739782
V2_RMSE=2.7300312262631214

V2_OVER_V1_MSE_RATIO=1.0000000185266333
V2_MSE_CHANGE_PERCENT=1.85266333386e-06

V2_VS_V1_RECON_RMSE=0.00055172040154353996

V1_MAX_ABS_ERROR=42.965518530752206
V2_MAX_ABS_ERROR=42.965499177018614

V2_VS_V1_MAX_ABS_DIFF=0.28601979398086996
```

### LINEAR

```text
V1_RMSE=2.687031038567345
V2_RMSE=2.6870311112627121

V2_OVER_V1_MSE_RATIO=1.0000000541083205
V2_MSE_CHANGE_PERCENT=5.41083204908e-06

V2_VS_V1_RECON_RMSE=0.0035409648009334118

V1_MAX_ABS_ERROR=41.677467480582891
V2_MAX_ABS_ERROR=41.67748789547386

V2_VS_V1_MAX_ABS_DIFF=1.8358195631620902
```

### RANDOM WALK

```text
V1_RMSE=10.623534924101518
V2_RMSE=10.623534850942237

V2_OVER_V1_MSE_RATIO=0.99999998622694186
V2_MSE_CHANGE_PERCENT=-1.37730581384e-06

V2_VS_V1_RECON_RMSE=1.0200820064298021e-05

V1_MAX_ABS_ERROR=404.78551872349408
V2_MAX_ABS_ERROR=404.78565010548255

V2_VS_V1_MAX_ABS_DIFF=0.00027538269023352768
```

The largest V2-vs-V1 pointwise difference occurs in the LINEAR stratum.

This observation does not reopen the M2.3 selection. M2.3 evaluated the
metadata-precision candidates under the frozen protocol and selected L32
before physical freeze. This document records the subsequent end-to-end
corpus behaviour of that already-selected representation.

---

## 10. Per-case saving distribution

Observed physical-file saving per canonical case:

```text
minimum  = 128 bytes
p50      = 128 bytes
p95      = 512 bytes
p99      = 512 bytes
maximum  = 512 bytes
```

The discrete saving values follow directly from the number of segments in each
case and the 32-byte per-segment difference between V1 and V2.

---

## 11. Empirical interpretation

The canonical-corpus result is:

```text
64-byte V1 metadata
        ↓
32-byte V2 L32 metadata
        ↓
374400 bytes theoretical metadata saving
        ↓
374400 bytes observed total wire saving
```

with:

```text
residual payload penalty = 0 bytes
other wire delta         = 0 bytes
```

The physical-layout optimization therefore transfers **1:1** into actual wire
size on the canonical corpus.

The observed corpus-size reduction is:

```text
19.966402688%
```

while the aggregate reconstruction distortion is effectively unchanged at the
scale measured here.

---

## 12. Completed cycle

The development and validation cycle represented by this evidence is:

```text
selection
    ↓
freeze
    ↓
implementation
    ↓
public interface
    ↓
empirical validation
```

Concrete state:

```text
M2.3_SELECTION=L32
M2.3_SELECTION_STATUS=CLOSED

M2.4_PHYSICAL_LAYOUT=<IIIfffff>
M2.4_SEGMENT_ENTRY_BYTES=32
M2.4_PHYSICAL_FREEZE_STATUS=SEALED

V2_WIRE_IMPLEMENTATION=COMMITTED
V2_PUBLIC_INTERFACE=COMMITTED

V1_REFERENCE_BYTE_IDENTITY=1575/1575
V2_DETERMINISM=1575/1575

CANONICAL_V1_BYTES=1875150
CANONICAL_V2_BYTES=1500750
CANONICAL_BYTES_SAVED=374400
CANONICAL_PERCENT_SAVED=19.966402688

RESIDUAL_PAYLOAD_DELTA_BYTES=0
NONMETADATA_NET_EFFECT_BYTES=0

EMPIRICAL_VALIDATION=PASS
```

This closes the current V2 physical-layout validation cycle.

Any future work may build on this result, but changing the frozen V2 physical
layout or reopening the candidate selection is outside the scope of this
evidence document and must follow the applicable protocol revision policy.
