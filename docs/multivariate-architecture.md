# Multivariate time-series architecture

Date: 2026-10-05

Issue:

```text
#10 research: define the architecture for multivariate time-series support
```

Status:

```text
ARCHITECTURE FROZEN
NO V2 WIRE CHANGE
```

## Decision summary

Lasagna SHALL distinguish two different problems:

```text
A. multichannel packaging
B. cross-channel compression
```

They are not the same feature.

The recommended architecture is:

```text
independent multichannel packaging
    ->
higher-level container around ordinary V2 streams

cross-channel prediction / shared modeling
    ->
future V3 codec semantics
```

V2 remains univariate and unchanged.

## Why V2 remains univariate

The current logical model is:

```text
TimeSeries {
    values: List[float]
    dt: float
    t0: str
    unit: str
}
```

The V2 wire assumes one logical signal:

```text
one n_points
one n_segments
one segment table
one residual section
one sampling context
one unit
```

Segmentation operates over one `values` sequence.

Predictor selection operates over one segment from one sequence.

Quantization and residual reconstruction are defined per one sequence.

Therefore adding channels inside V2 would not be a metadata-only extension.

It would alter the meaning of:

```text
n_points
n_segments
segment ownership
residual-block ownership
sampling metadata
unit metadata
predictor dependencies
```

Such a change is outside the compatibility boundary of V2.

## Architectural decomposition

### Layer 1 — univariate codec

Existing Lasagna V2 remains:

```text
TimeSeries
    ->
V2 encoder
    ->
one self-contained univariate .lsg2 stream
```

No multivariate semantics are added here.

### Layer 2 — multichannel container

A future higher-level container MAY package multiple independent V2 streams:

```text
MultivariateSeries
    ->
channel directory
    ->
channel 0 -> complete V2 stream
channel 1 -> complete V2 stream
...
channel N -> complete V2 stream
```

This layer handles:

```text
channel identity
channel metadata
alignment declarations
per-channel sampling metadata
missing-value policy
stream offsets / lengths
container-level metadata
```

Each contained V2 stream remains independently decodable.

### Layer 3 — future multivariate codec

Cross-channel prediction belongs to a future V3 design.

Examples:

```text
channel B predicted from channel A
shared latent predictor state
shared segment boundaries
joint residual modeling
cross-channel transforms
```

These mechanisms create semantic dependencies between channels.

They therefore cannot be represented as merely a container concern.

## Minimal logical data model

The research model SHALL distinguish dataset-level metadata from channel-level
metadata.

```text
MultivariateTimeSeries {
    channels: List[Channel]
    alignment: AlignmentPolicy
}
```

Each channel:

```text
Channel {
    channel_id: str
    name: str
    values: List[float | Missing]
    unit: str
    sampling: Sampling
}
```

Sampling:

```text
Sampling {
    dt: float | None
    t0: str | None
    timestamps: List[Timestamp] | None
}
```

Constraints:

```text
exactly one sampling representation is active:

regular:
    dt + t0

or

explicit:
    timestamps
```

The initial packaging design SHOULD support regular sampling first.

Explicit irregular timestamps remain an extension point.

## Channel identity

Every channel SHALL have a stable container-local identifier.

Example:

```text
temperature
humidity
pressure
```

Requirements:

```text
non-empty
unique within container
independent of display name
```

Display names MAY be non-unique metadata.

Codec behavior SHALL reference `channel_id`, not display name.

## Channel metadata

Minimum channel metadata:

```text
channel_id
unit
sampling description
sample count
payload location
payload length
payload format/version
```

Optional descriptive metadata MAY include:

```text
name
description
sensor/source identifier
domain-specific tags
```

Optional descriptive metadata SHALL NOT affect decode semantics.

## Sampling model

Multivariate support SHALL NOT assume that all channels necessarily have the
same sampling configuration.

Two modes are distinguished.

### Shared regular sampling

All channels have:

```text
same t0
same dt
same sample count
```

This is the simplest aligned case.

Container metadata MAY store shared sampling once.

### Per-channel regular sampling

Each channel may have its own:

```text
t0
dt
sample count
```

Each contained V2 stream already carries these values independently.

The container SHALL NOT silently claim sample-index alignment in this mode.

## Alignment semantics

Alignment SHALL be explicit metadata.

Initial policies:

```text
ALIGNED_INDEX
INDEPENDENT
```

### ALIGNED_INDEX

Requirements:

```text
same t0
same dt
same sample count
```

Meaning:

```text
sample i in every channel represents the same logical instant
```

### INDEPENDENT

No sample-index correspondence is implied.

Channels merely coexist in one container.

Future designs MAY add:

```text
TIMESTAMP_ALIGNED
```

but that requires explicit timestamp semantics beyond current V2.

## Missing-value semantics

Current V2 encodes finite numeric univariate values and has no first-class
missing-value representation.

Therefore the container SHALL NOT invent NaN-based missing semantics inside a
V2 payload.

For independent V2 packaging, the first frozen rule is:

```text
contained V2 streams MUST themselves satisfy ordinary V2 numeric validity
```

If a source multivariate dataset contains missing values, preprocessing policy
MUST be explicit before V2 encoding.

Possible source-level policies include:

```text
reject
drop aligned row
impute
split into independently valid spans
external validity bitmap
```

No one of these becomes implicit codec behavior in issue #10.

An external validity bitmap would itself require container wire design and
therefore remains future work.

## Segmentation architecture

Two fundamentally different models exist.

### Independent segmentation

Each channel is encoded independently:

```text
channel A:
    boundaries A

channel B:
    boundaries B

channel C:
    boundaries C
```

Advantages:

```text
reuses V2 unchanged
channel-local optimization
independent decode
simple random access
simple streaming
failure isolation
```

Disadvantages:

```text
no shared-boundary compression
no cross-channel predictor coordination
duplicate metadata may remain
```

This is the recommended model for the container layer.

### Shared segmentation

All aligned channels use one common set of segment boundaries:

```text
[start0, end0]
[start1, end1]
...
```

Advantages may include:

```text
shared metadata
cross-channel modeling
simpler synchronized windows
```

Costs:

```text
one difficult channel may force boundaries for all channels
channel-local optimum is lost
joint optimization is required
predictor semantics become multivariate
```

Shared segmentation therefore belongs to V3 research.

It SHALL NOT be imposed by the independent-container layer.

## Predictor architecture

### Independent predictors

Container packaging uses ordinary V2 predictors independently per channel.

Conceptually:

```text
x_c(t)
    ->
predictor_c
    ->
residual_c
```

No new predictor semantics are required.

### Cross-channel predictors

Future V3 MAY support:

```text
x_B(t) = f(x_A(t), history_B, ...)
```

or more generally:

```text
x_c(t) = f(
    own history,
    other channel values/history,
    shared state
)
```

Such predictors require explicit dependency metadata.

At minimum a future design would need:

```text
target channel
source channel(s)
dependency order
predictor identifier
predictor parameters
decode ordering
```

Cycles MUST either:

```text
be forbidden
```

or require a jointly decodable model.

The initial recommendation is:

```text
future cross-channel dependency graph MUST be acyclic
```

unless a later V3 design proves a deterministic cyclic reconstruction model.

## Decode dependency graph

Independent container:

```text
no channel dependencies
```

Each channel can be decoded separately.

Future V3:

```text
channel dependency graph
```

Decode order becomes part of the format semantics.

This is another reason cross-channel prediction cannot be an invisible V2
extension.

## Layout alternatives evaluated

### Alternative A — extend V2 with a channel count

Concept:

```text
existing V2 header
+
channel_count
+
channel-aware segment/residual tables
```

Decision:

```text
REJECT
```

Reason:

A channel count alone does not define:

```text
segment ownership
sampling ownership
units
alignment
missing values
prediction dependencies
residual ordering
```

The resulting stream would use V2 framing with non-V2 semantics.

That is version ambiguity.

### Alternative B — interleaved channel samples

Concept:

```text
A0 B0 C0 A1 B1 C1 ...
```

Decision:

```text
REJECT AS BASELINE ARCHITECTURE
```

Advantages:

```text
temporal adjacency across aligned channels
```

Disadvantages:

```text
destroys ordinary V2 univariate semantics
poor independent-channel access
couples segmentation and channel count
different units share one logical sample stream
cross-channel meaning remains implicit
```

If ever used, it belongs to a future multivariate codec.

### Alternative C — columnar channels inside one new codec stream

Concept:

```text
global header
channel metadata
channel segment tables
channel residual sections
```

Decision:

```text
DEFER TO V3
```

This is a plausible native multivariate codec architecture but requires a new
wire-format contract.

### Alternative D — container of independent V2 streams

Concept:

```text
container header
channel directory
V2 stream
V2 stream
...
```

Decision:

```text
RECOMMENDED FOR INITIAL MULTIVARIATE PACKAGING
```

Advantages:

```text
V2 remains immutable
existing encoder reused
existing decoder reused
per-channel random access
per-channel streaming
per-channel corruption isolation
mixed future contained versions possible
simple migration path
```

Trade-off:

```text
does not exploit cross-channel statistical redundancy
```

That limitation is intentional.

Packaging and cross-channel compression are separate concerns.

## Container boundary

The future container SHALL have its own:

```text
magic
version
channel count
directory
metadata
```

It SHALL NOT masquerade as an ordinary `.lsg2` V2 file.

Conceptual layout:

```text
+-----------------------------+
| multichannel container hdr  |
+-----------------------------+
| shared metadata             |
+-----------------------------+
| channel directory           |
+-----------------------------+
| channel 0 V2 bytes          |
+-----------------------------+
| channel 1 V2 bytes          |
+-----------------------------+
| ...                         |
+-----------------------------+
```

Directory entries need at minimum:

```text
channel_id
offset
length
contained_format
contained_version
```

Channel-specific descriptive metadata MAY live either:

```text
in directory-associated metadata
or
in a dedicated metadata region
```

The exact physical wire layout is NOT frozen by issue #10.

## Backward compatibility

### Existing V1 files

Unchanged.

### Existing V2 files

Unchanged.

### Existing decode_timeseries()

Continues to mean:

```text
decode one univariate Lasagna stream
```

It SHALL NOT silently begin returning a multivariate object.

### Future multichannel container

Requires an explicit API such as conceptually:

```text
encode_multivariate(...)
decode_multivariate(...)
```

or a separate container module.

Univariate callers therefore retain their existing type contract.

## Compatibility matrix

```text
old V1 decoder -> V1: yes
old V1 decoder -> V2: no

current unified decoder -> V1: yes
current unified decoder -> V2: yes

current unified decoder -> future multichannel container: no

future container decoder -> contained V1/V2:
possible by explicit dispatch policy
```

The recommended initial container SHOULD restrict contained streams to V2
unless a concrete compatibility requirement justifies mixed versions.

## Random access

Independent-container architecture permits channel-level random access if the
directory stores byte offsets and lengths.

Conceptually:

```text
find channel_id
seek offset
read length
decode contained V2 stream
```

This is substantially simpler than a cross-channel codec, where decoding one
channel may require predecessor channels.

Segment-level random access remains whatever the contained V2 format supports.

The container does not worsen it.

## Streaming

Independent V2 streams can be encoded channel-by-channel.

A streaming writer could:

```text
reserve/write directory metadata
emit each channel stream
finalize offsets/lengths
```

or use a footer/index design.

A streaming reader can decode a channel once its complete contained stream is
available.

Cross-channel prediction would impose stronger ordering constraints and is
therefore deferred to V3.

## Corruption isolation

Independent contained streams provide a useful failure boundary.

Conceptually:

```text
channel A corrupt
!=
channel B necessarily corrupt
```

Container directory corruption remains a container-level failure mode.

A future wire design SHOULD consider:

```text
directory integrity
per-channel checksums
container checksum
```

but issue #10 does not freeze checksum semantics.

## Units

Units are channel-local.

Example:

```text
temperature -> degC
humidity    -> %
pressure    -> hPa
```

A multivariate architecture MUST NOT assume one global unit.

Shared unit metadata MAY be deduplicated as an optimization only if semantics
remain equivalent.

## Channel ordering

Physical channel order SHALL NOT define semantic dependency.

Channel identity is carried by `channel_id`.

For independent packaging, reordering directory entries SHALL NOT change the
decoded logical dataset.

For future cross-channel prediction, dependencies SHALL be explicit rather
than inferred from physical order.

## Minimal validation invariants

A future multivariate logical model SHALL reject:

```text
zero channels
duplicate channel_id values
empty channel_id
invalid sampling metadata
alignment=ALIGNED_INDEX with unequal sample counts
alignment=ALIGNED_INDEX with unequal dt
alignment=ALIGNED_INDEX with unequal t0
non-finite values passed directly to ordinary V2
```

For `INDEPENDENT` alignment, sample counts and sampling configurations may
differ.

## Separation of concerns

The architecture SHALL preserve:

```text
container
    !=
codec

channel packaging
    !=
cross-channel prediction

alignment metadata
    !=
shared segmentation

shared segmentation
    !=
cross-channel prediction
```

This separation is the central design rule of issue #10.

## Recommended implementation sequence

### Phase 1 — container-only support

Future implementation issue:

```text
minimal MultivariateTimeSeries model
independent V2 channel encoding
container directory
channel metadata
ALIGNED_INDEX / INDEPENDENT validation
channel-level random access
```

No cross-channel compression.

### Phase 2 — research cross-channel structure

Separate research issue:

```text
measure real inter-channel correlation
compare independent V2 size
evaluate cross-channel predictors
evaluate shared segmentation
measure dependency cost
measure random-access degradation
```

No production V3 before evidence.

### Phase 3 — V3 only if justified

A V3 format becomes justified only if cross-channel modeling shows measurable
benefit large enough to repay:

```text
dependency metadata
shared-model metadata
more complex decode
reduced random access
reduced failure isolation
implementation complexity
```

## Final recommendation

### Simple multivariate packaging

Use:

```text
SEPARATE HIGHER-LEVEL CONTAINER
```

containing independent V2 streams.

### Cross-channel prediction

Use:

```text
FUTURE V3
```

if and only if research demonstrates measurable benefit.

### V2

Decision:

```text
KEEP V2 UNCHANGED
```

## Issue #10 acceptance mapping

Architectural alternatives documented:

```text
PASS
```

Backward compatibility explicit:

```text
PASS
```

Cross-channel prediction separated from channel packaging:

```text
PASS
```

Minimal multivariate model specified:

```text
PASS
```

No V2 wire change:

```text
PASS
```

Implementation boundary recommendation:

```text
container for independent packaging
V3 for cross-channel codec semantics
```

## Architecture gates

```text
MULTIVARIATE_DATA_MODEL_GATE=PASS
CHANNEL_METADATA_GATE=PASS
SAMPLING_MODEL_GATE=PASS
ALIGNMENT_SEMANTICS_GATE=PASS
MISSING_VALUE_BOUNDARY_GATE=PASS
SEGMENT_SYNCHRONIZATION_GATE=PASS
CROSS_CHANNEL_PREDICTION_BOUNDARY_GATE=PASS
CONTAINER_ALTERNATIVES_GATE=PASS
BACKWARD_COMPATIBILITY_GATE=PASS
RANDOM_ACCESS_GATE=PASS
STREAMING_GATE=PASS

V2_WIRE_CHANGE_GATE=REJECT
INDEPENDENT_MULTICHANNEL_CONTAINER_GATE=RECOMMEND
CROSS_CHANNEL_V3_GATE=RESEARCH_REQUIRED
```
