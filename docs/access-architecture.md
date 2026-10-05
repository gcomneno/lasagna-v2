# Random access, streaming and partial-decode architecture

Date: 2026-10-05

Issue:

```text
#11 design: define random access, streaming and partial-decode support
```

Status:

```text
ARCHITECTURE FROZEN
NO V2 WIRE CHANGE
```

## Decision summary

Lasagna SHALL treat the following as three separate capabilities:

```text
random access
streaming
partial decode
```

They are related but not equivalent.

The frozen architecture is:

```text
immutable standalone V2
    +
optional derived external index
    ->
segment lookup
    ->
segment-level partial decode
```

A future embedded index requires an explicitly versioned container or wire
revision.

V2 itself remains unchanged.

## Current V2 physical layout

Conceptually:

```text
FILE_HEADER
CONTEXT_JSON
SEGMENT_TABLE
RESIDUAL_SECTION_HEADER
RESIDUAL_BLOCK_0
RESIDUAL_BLOCK_1
...
RESIDUAL_BLOCK_N
```

The file header contains:

```text
header_len
n_points
n_segments
```

The V2 segment table contains one fixed-width 32-byte entry per segment:

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

Each residual block contains a fixed-width header:

```text
seg_id
seg_len
byte_len
```

followed by exactly:

```text
byte_len
```

payload bytes.

## Important existing property

Residual blocks are already self-delimiting.

Given the byte offset of a residual block header:

```text
read 12-byte block header
obtain seg_id
obtain seg_len
obtain byte_len
read exactly byte_len payload bytes
```

Therefore V2 does not need a new residual framing format for segment-level
partial decoding.

The missing capability is efficient lookup of the block offset.

## Current limitation

The segment table is fixed-width and therefore directly addressable.

For segment `i`:

```text
segment_entry_offset =
    file_header_size
    + header_len
    + i * segment_entry_size
```

Residual blocks are variable-width.

V2 stores no residual-block offset directory.

Therefore locating residual block `i` currently requires:

```text
start at residual section
scan block headers 0 .. i-1
sum header + byte_len
```

Complexity:

```text
O(i)
```

for one uncached lookup.

A complete one-time scan can derive offsets for all blocks in:

```text
O(n_segments)
```

time.

## Random access definition

For issue #11, random access means:

```text
Given a logical sample range or segment identifier,
locate and decode only the residual segment(s) required for that request
without reconstructing unrelated segments.
```

Random access does NOT mean:

```text
arbitrary byte seek without metadata
```

and does NOT imply:

```text
single-sample decode with zero segment overhead
```

## Partial decode granularity

The frozen native partial-decode unit is:

```text
ONE COMPLETE SEGMENT
```

Reason:

```text
segment metadata is segment-scoped
quantization is segment-scoped
residual framing is segment-scoped
predictor initialization is segment-scoped
```

### Mean predictor

A complete segment can be reconstructed from:

```text
segment metadata
+
that segment residual block
```

No preceding segment is required.

### Linear predictor

Same property:

```text
segment metadata
+
that segment residual block
```

is sufficient.

### Random-walk predictor

Random-walk reconstruction has an intra-segment recurrence:

```text
x_hat[i]
depends on
x_hat[i - 1]
```

but the segment stores:

```text
seed_value
```

Therefore reconstruction starts independently at the beginning of each
segment.

A random-walk segment does NOT require any preceding segment.

However, decoding one arbitrary sample in the middle of a random-walk segment
requires reconstruction from that segment's beginning up to the target sample.

Thus:

```text
segment-level random access:
YES

arbitrary sample-level O(1) random access:
NO
```

## Range decode semantics

A future API MAY conceptually expose:

```text
decode_range(start_idx, end_idx)
```

with inclusive sample indices.

Semantics:

```text
1. identify every segment intersecting [start_idx, end_idx]
2. decode each complete intersecting segment
3. trim decoded values to the requested logical range
4. return the requested samples in original order
```

The decoder MAY decode extra samples at the boundaries because segment
reconstruction is the native unit.

Example:

```text
requested:
samples 50..90

segments:
32..63
64..95

physical decode:
32..95

returned:
50..90
```

This is still partial decode because unrelated segments are not decoded.

## Segment selection

Because the segment table is contiguous and ordered by logical sample range,
an implementation can identify intersecting segments from:

```text
start_idx
end_idx
```

A basic implementation may scan the segment table.

A cached/indexed implementation may binary-search by logical range.

## Index architecture

The recommended first index is:

```text
EXTERNAL / DERIVED / OPTIONAL
```

It is not part of the V2 byte stream.

Conceptual model:

```text
V2Index {
    source_identity
    format_version
    n_points
    n_segments
    residual_section_offset
    entries[]
}
```

Each entry:

```text
V2IndexEntry {
    seg_id
    start_idx
    end_idx
    segment_entry_offset
    residual_block_offset
    residual_payload_offset
    residual_payload_length
}
```

## Minimum required fields

### seg_id

Stable association between:

```text
segment table entry
residual block
index entry
```

### start_idx / end_idx

Required for logical range lookup.

### segment_entry_offset

Allows direct metadata reads without reparsing the whole segment table.

This field is technically derivable because entries are fixed-width, but
storing it simplifies a generic index and permits integrity checks.

### residual_block_offset

Direct location of:

```text
seg_id
seg_len
byte_len
```

### residual_payload_offset

Direct location of encoded residual bytes.

This is derivable from:

```text
residual_block_offset
+
RESIDUAL_BLOCK_HEADER_STRUCT.size
```

but MAY be stored explicitly for convenience.

### residual_payload_length

Equivalent to block header `byte_len`.

Storing it in the index allows consistency validation before decode.

## Derived-index construction

An index builder for existing V2 requires only one sequential metadata scan.

Algorithm:

```text
read file header
read/skip context JSON
parse fixed-width segment table
read residual section header

for each residual block:
    record current block offset
    read seg_id, seg_len, byte_len
    record payload offset/length
    skip byte_len
```

No residual payload needs to be decoded.

Therefore index construction cost is:

```text
O(file metadata + number of residual block headers)
```

rather than full numeric decode.

## Source identity

An external index MUST be bound to one exact source stream.

At minimum the index needs a strong source identity.

Recommended options:

```text
file size + cryptographic hash
```

or:

```text
cryptographic hash alone
```

The exact serialization is deferred.

An index whose source identity does not match the V2 stream MUST be rejected.

This prevents stale offsets from being applied to a different file.

## Index validation

Before use, a derived index SHOULD verify at least:

```text
source identity
format_version == 2
n_points
n_segments
entry count
seg_id uniqueness
segment range consistency
payload offsets within source size
payload lengths within source size
```

Optional strict validation may also compare:

```text
segment start/end against source segment table
block seg_id against source block header
block byte_len against indexed payload length
```

## External index advantages

```text
zero V2 compatibility impact
works with already-existing V2 files
can be created lazily
can be deleted/rebuilt
does not burden small files
permits application-specific persistence
```

## External index disadvantages

```text
second artifact to manage
stale-index risk
source/index association required
not self-contained
```

These are acceptable for the first access architecture because V2 remains
immutable.

## Embedded index alternative

An index embedded inside an ordinary existing V2 stream is NOT approved.

Appending bytes silently to V2 would create ambiguity around:

```text
end-of-stream semantics
integrity
old decoder behavior
index discovery
future extensions
```

Reusing currently reserved header fields without an explicit wire revision is
also rejected.

Therefore:

```text
EMBEDDED INDEX IN FROZEN V2 = REJECT
```

A future self-contained indexed representation requires either:

```text
a new wire revision
```

or:

```text
a higher-level container
```

with explicit index semantics.

## Sidecar serialization

Issue #11 freezes the logical index model, not its permanent binary encoding.

A prototype sidecar MAY initially use:

```text
JSON
```

for inspectability or:

```text
a compact deterministic binary form
```

for production.

Whichever representation is later chosen MUST preserve the same semantic
fields and source-binding rules.

## Random-access complexity

### No index

For one target residual block:

```text
segment metadata lookup:
O(1) by fixed-width table offset

residual block lookup:
O(i) scan to segment i
```

### Derived in-memory index

Initial build:

```text
O(n_segments)
```

Subsequent block lookup:

```text
O(1) by seg_id
```

Logical sample-range lookup:

```text
O(log n_segments)
```

with sorted range entries and binary search, or:

```text
O(n_segments)
```

with a simple scan.

### Persisted sidecar index

Startup lookup:

```text
index parse cost
```

followed by:

```text
O(1) residual seek by seg_id
```

without scanning the V2 residual section.

## Streaming is a separate problem

Random access assumes:

```text
seekable source
```

Streaming assumes:

```text
bytes arrive progressively
source may be non-seekable
```

An index does not automatically solve streaming.

## Current V2 decode streaming

The current public decoder:

```text
decode_timeseries(data: bytes)
```

requires the complete byte string before decoding.

Therefore the current API is:

```text
NOT incrementally streaming
```

This is an implementation/API limitation.

The V2 wire itself has more useful structure than the current API exposes.

## V2 wire streaming properties

V2 is ordered as:

```text
header
context
complete segment table
residual section
residual blocks
```

Before residual data begins, the decoder knows:

```text
n_points
n_segments
all segment metadata
residual coding type
```

Residual blocks then arrive one at a time with explicit:

```text
seg_id
seg_len
byte_len
```

Therefore a streaming decoder can conceptually:

```text
1. buffer fixed file header
2. buffer context JSON
3. buffer segment table
4. read residual section header
5. for each residual block:
       buffer one block header
       buffer exactly byte_len payload bytes
       decode residual block
       reconstruct corresponding segment
       emit reconstructed segment
```

It does NOT need the complete residual section in memory.

## Streaming decoder memory bound

After metadata has been received, residual decode working memory can be bounded
approximately by:

```text
segment table
+
one residual block
+
one reconstructed segment
+
small codec state
```

A future implementation need not allocate:

```text
all residual blocks
+
full reconstructed n_points array
```

unless the caller explicitly asks for a complete `TimeSeries`.

## Segment table streaming cost

The complete segment table occurs before the residual section.

Therefore current V2 requires receiving:

```text
header
+
context
+
entire segment table
+
residual section header
```

before the first segment payload can be reconstructed.

For current small segment entries this is acceptable but it means V2 is not
"sample-immediate" streaming.

The metadata prefix grows as:

```text
O(n_segments)
```

## Streaming encode

Current V2 encoding is NOT truly streaming.

The encoder first builds:

```text
all segmentation
all segment metadata
all quantized residual segments
```

before writing the final file.

More fundamentally, adaptive segmentation requires lookahead over candidate
segments.

Section-level residual mode:

```text
residual_coding = auto
```

also compares aggregate varint and zero-run payload sizes for the whole
residual section before choosing one global coding type.

Therefore current encoder semantics require whole-series or at least
whole-section knowledge.

## Streaming encode levels

The architecture distinguishes:

### Level S0 — current

```text
whole TimeSeries in memory
whole encoded bytes returned
```

### Level S1 — streaming output after analysis

Encoder may analyze the complete series first, but write the finalized V2
bytes incrementally to a sink.

This reduces duplicate output buffering but is not online encoding.

Possible without changing V2 semantics.

### Level S2 — online segment encoding

Input samples arrive progressively and finalized segments are emitted before
the complete series is known.

This is incompatible with some current global decisions, especially:

```text
section-level residual auto
final n_points
final n_segments
complete segment table before residual section
```

Achieving S2 cleanly therefore requires a different container/layout or wire
revision.

## Recommended streaming boundary

For frozen V2:

```text
streaming decode:
architecturally feasible

streaming output after full analysis:
architecturally feasible

true online encode:
NOT a V2 requirement
```

A future online format may use:

```text
chunk/page framing
local headers
periodic indexes
footer index
```

but such a design is outside frozen V2.

## Partial-decode API architecture

Recommended conceptual API:

```text
index = build_v2_index(source)

segment = decode_segment(
    source,
    index,
    seg_id,
)

subset = decode_range(
    source,
    index,
    start_idx,
    end_idx,
)
```

`source` should conceptually support:

```text
read_at(offset, length)
```

rather than requiring one complete in-memory `bytes` value.

Possible concrete source types later:

```text
bytes
memoryview
seekable file
mmap
application-provided random-access reader
```

The architecture SHOULD avoid making filesystem paths part of codec semantics.

## decode_segment semantics

Input:

```text
V2 source
validated V2Index
seg_id
```

Operation:

```text
read one segment metadata entry
read one residual block
decode residual integers
reconstruct exactly that complete logical segment
```

Output conceptually includes:

```text
segment start index
segment end index
decoded values
sampling context
unit
```

It does not return a fake standalone TimeSeries beginning at index zero unless
the API explicitly defines rebasing.

## decode_range semantics

Input:

```text
start_idx
end_idx
```

Validation:

```text
0 <= start_idx <= end_idx < n_points
```

Operation:

```text
find intersecting segments
decode each complete intersecting segment
trim first and last segment
concatenate requested values
```

Output metadata MUST preserve the logical starting position.

For regular sampling:

```text
range_t0 =
    original_t0
    + start_idx * dt
```

if the implementation exposes a rebased `TimeSeries`.

Alternatively a dedicated range result may retain:

```text
original_start_idx
```

The API design MUST choose explicitly; it must not silently lose positional
meaning.

## Empty ranges

The initial recommendation is:

```text
reject empty range
```

rather than introduce ambiguous inclusive/exclusive semantics.

A later Pythonic half-open API:

```text
[start, stop)
```

may be preferable for implementation, but issue #11 freezes only the logical
semantics, not the final Python spelling.

## Corruption behavior

Partial decode MUST fail closed for any structure it consumes.

At minimum validate:

```text
source identity
segment metadata bounds
residual block bounds
seg_id agreement
seg_len agreement
payload length
residual codec validity
decoded residual count
```

Partial decode does not need to validate unrelated residual payloads.

Therefore corruption in an unrelated segment SHOULD NOT prevent decoding a
valid target segment if:

```text
the global header
context
segment table
index
target residual block
```

remain valid.

This is a useful semantic difference from full-file validation.

## Integrity scope

A future index/container may support:

```text
whole-file checksum
per-page checksum
per-segment checksum
```

Issue #11 does not freeze checksum layout.

However strong partial-corruption isolation favors:

```text
smaller integrity domains
```

over only one whole-file checksum.

This is future wire/container work.

## Backward compatibility

Existing V2 bytes remain unchanged.

Existing:

```text
decode_timeseries(data)
```

continues to perform whole-series decode.

New access APIs MAY be added later without changing encoded V2 bytes.

Existing files can gain random access simply by:

```text
building an index after the fact
```

No migration or re-encoding is required.

## Relationship to issue #10 container architecture

Issue #10 recommended a higher-level multichannel container with a channel
directory.

The same design principle applies here:

```text
directory/index structures
belong above immutable V2 when possible
```

A future container could carry:

```text
channel directory
+
per-channel V2 index
+
contained V2 streams
```

without modifying the contained streams.

## Relationship to issue #9 entropy result

Issue #9 showed that larger coding groups may improve compression but trade
against random-access granularity.

Issue #11 makes that trade explicit:

```text
smaller independent segments/pages
    ->
better random access
    ->
more framing/compression overhead

larger coding groups
    ->
better compression opportunity
    ->
coarser partial decode
```

Future format work MUST report both dimensions.

## Alternatives evaluated

### A. Do nothing; scan residual blocks for every request

Decision:

```text
VALID FALLBACK
NOT RECOMMENDED AS RANDOM-ACCESS ARCHITECTURE
```

Useful for one-off access to small files.

Poor for repeated queries.

### B. Build an in-memory derived index

Decision:

```text
RECOMMENDED BASELINE
```

Advantages:

```text
no wire change
simple
cheap one-time scan
O(1) block lookup afterward
```

### C. Persist the same index as a sidecar

Decision:

```text
RECOMMENDED OPTIONAL OPTIMIZATION
```

Especially useful for:

```text
large files
repeated sessions
remote object storage
```

provided source identity is verified.

### D. Embed an index into frozen V2

Decision:

```text
REJECT
```

Requires explicit format revision.

### E. New indexed/page-oriented format

Decision:

```text
DEFER
```

Potentially justified for:

```text
true online encoding
self-contained persistent indexes
page-level integrity
remote range requests
coarser entropy groups
```

but outside issue #11.

## Recommended implementation sequence

### Phase 1

Implement read-only V2 indexing utilities:

```text
parse_v2_index()
build_v2_index()
```

against existing bytes/seekable sources.

No wire mutation.

### Phase 2

Implement:

```text
decode_segment()
decode_range()
```

and verify equality against slices of full decode.

### Phase 3

Add streaming decoder abstraction:

```text
feed bytes
emit complete decoded segments
```

without changing V2.

### Phase 4

Only if justified by real workloads, research a new page/index container or
future wire revision for:

```text
online encode
embedded index
remote byte-range access
page-level integrity
larger entropy groups
```

## Acceptance mapping

Current limitations documented precisely:

```text
PASS
```

Random access and streaming separated:

```text
PASS
```

Index model proposed and evaluated:

```text
PASS
```

Backward compatibility addressed:

```text
PASS
```

Partial decode semantics specified:

```text
PASS
```

Frozen V2 modified:

```text
NO
```

## Architecture gates

```text
CURRENT_V2_LIMITATIONS_GATE=PASS
RANDOM_ACCESS_SEPARATION_GATE=PASS
STREAMING_SEPARATION_GATE=PASS
PARTIAL_DECODE_GRANULARITY_GATE=PASS
DERIVED_INDEX_MODEL_GATE=PASS
SOURCE_IDENTITY_GATE=PASS
BACKWARD_COMPATIBILITY_GATE=PASS
CORRUPTION_SCOPE_GATE=PASS

V2_EXTERNAL_INDEX_GATE=RECOMMEND
V2_PARTIAL_SEGMENT_DECODE_GATE=RECOMMEND
V2_STREAMING_DECODE_GATE=FEASIBLE
V2_STREAMING_OUTPUT_GATE=FEASIBLE
V2_TRUE_ONLINE_ENCODE_GATE=DEFER

FROZEN_V2_EMBEDDED_INDEX_GATE=REJECT
V2_WIRE_CHANGE_GATE=REJECT
```
