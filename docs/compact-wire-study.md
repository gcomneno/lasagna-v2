# Compact Wire Study (#26)

Does compact wire preserve V2 semantics while materially reducing actual serialized bytes?

Wire-layout validation; no codec-superiority claim or public format promotion.

Reporting repair: strict saved CSV parsing and canonical public compatibility fixtures; no corpus rerun. Original corpus provenance is unchanged. The separate `reporting_repair` entry records recovery inputs and command.

```json
{
  "compact_byte_reduction_summary": {
    "compact_total_bytes": 14955137,
    "max_total_reduction_fraction": 0.33345255334368507,
    "median_total_reduction_fraction": 0.2011661807580175,
    "min_total_reduction_fraction": 0.00014791852904671998,
    "total_byte_reduction": 4106771,
    "v2_total_bytes": 19061908
  },
  "execution_completed": true,
  "gates": {
    "baseline24_agreement_gate": true,
    "compact_timing_determinism_gate": true,
    "exact_byte_accounting_gate": true,
    "full_grid_execution_gate": true,
    "projection25_agreement_gate": true,
    "public_compatibility_gate": true,
    "semantic_equivalence_gate": true
  },
  "outcome": "PASS",
  "point_count": 385,
  "provenance": {
    "architecture_matrix": [
      {
        "architecture": "A0",
        "fixed_segment_length": null,
        "max_segment_length": null,
        "min_segment_length": null,
        "mse_threshold": null,
        "name": "whole_linear",
        "predictor": "linear",
        "segment_mode": "fixed"
      },
      {
        "architecture": "A1",
        "fixed_segment_length": 64,
        "max_segment_length": null,
        "min_segment_length": null,
        "mse_threshold": null,
        "name": "fixed_linear",
        "predictor": "linear",
        "segment_mode": "fixed"
      },
      {
        "architecture": "A2",
        "fixed_segment_length": 64,
        "max_segment_length": null,
        "min_segment_length": null,
        "mse_threshold": null,
        "name": "fixed_auto",
        "predictor": "auto",
        "segment_mode": "fixed"
      },
      {
        "architecture": "A3",
        "fixed_segment_length": null,
        "max_segment_length": 128,
        "min_segment_length": 32,
        "mse_threshold": 0.5,
        "name": "adaptive_linear",
        "predictor": "linear",
        "segment_mode": "adaptive"
      },
      {
        "architecture": "A4",
        "fixed_segment_length": null,
        "max_segment_length": 128,
        "min_segment_length": 32,
        "mse_threshold": 0.5,
        "name": "adaptive_auto",
        "predictor": "auto",
        "segment_mode": "adaptive"
      }
    ],
    "baseline24_artifact_sha256": {
      "docs/local-model-value-matched.csv": "b27d3d1c171a0edbbd2984798623ee74295e59555b64217142f9d1c7b50a6ae4",
      "docs/local-model-value-protocol.md": "75d29c40f653e8af43e798e6801eea6f1cbf1d333a275ad24815ccb2463cbbd1",
      "docs/local-model-value-provenance.json": "51b095f449a74936b0584bc46ee7f29d7f1ce48d1216636f949e4eb6d5abf383",
      "docs/local-model-value-results.csv": "d18d01b3994233bef4f8d84915778f84c94c26225c8fc76a76e5d1325b6a40a7",
      "docs/local-model-value-study.md": "c3abf9d54ee9be98476e4a1340ee870014d572769a2dfa92d6a03be94df89109",
      "docs/local-model-value-summary.csv": "87583353bb503290b90f4179f2abf897d84b186e871e227d663f37552fbd9f0a"
    },
    "baseline24_protocol_freeze_commit": "198c8fd3434360c405d15a3e2a353dab039ca1ec",
    "baseline24_protocol_sha256": "75d29c40f653e8af43e798e6801eea6f1cbf1d333a275ad24815ccb2463cbbd1",
    "baseline24_verified_protocol_freeze_commit": "198c8fd3434360c405d15a3e2a353dab039ca1ec",
    "codec_source_identity": {
      "path": "lasagna2/core.py",
      "sha256": "b9db63d5b4b37117e9eb2f55b21c0d75cabddd0ed3c195b6d4468981821c2a48"
    },
    "command": ".venv/bin/python tools/benchmark_compact_wire.py --mode corpus",
    "command_line": [
      ".venv/bin/python",
      "tools/benchmark_compact_wire.py",
      "--mode",
      "corpus"
    ],
    "compact_prototype_identity": {
      "path": "lasagna2/experimental_compact.py",
      "sha256": "3274f3795d3544f69745e43d988b7359f6cff58a2db6538c830a662e73e508fe"
    },
    "configurations": {
      "A0": [
        {
          "C_Q": 0.0625,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.125,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.25,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.5,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 1.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 2.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        },
        {
          "C_Q": 4.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": "n_samples",
          "segment_mode": "fixed"
        }
      ],
      "A1": [
        {
          "C_Q": 0.0625,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.125,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.25,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.5,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 1.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 2.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 4.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        }
      ],
      "A2": [
        {
          "C_Q": 0.0625,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.125,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.25,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 0.5,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 1.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 2.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        },
        {
          "C_Q": 4.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "fixed"
        }
      ],
      "A3": [
        {
          "C_Q": 0.0625,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.125,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.25,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.5,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 1.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 2.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 4.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "linear",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        }
      ],
      "A4": [
        {
          "C_Q": 0.0625,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.125,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.25,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 0.5,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 1.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 2.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        },
        {
          "C_Q": 4.0,
          "Q_MIN": 1e-06,
          "max_segment_length": 128,
          "min_segment_length": 32,
          "mse_threshold": 0.5,
          "predictor": "auto",
          "residual_coding": "varint",
          "segment_length": 64,
          "segment_mode": "adaptive"
        }
      ]
    },
    "cpu_identity": "Intel(R) Core(TM) i3-4330 CPU @ 3.50GHz",
    "dataset_order": [
      {
        "evidence_group": "internal",
        "path": "data/examples/trend.csv"
      },
      {
        "evidence_group": "internal",
        "path": "data/examples/sine_noise.csv"
      },
      {
        "evidence_group": "internal",
        "path": "data/examples/flat_spike.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/appliances-energy.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/metro-traffic.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/beijing-pm25.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/seoul-bike-demand.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/fan-vibration-x.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/dow-jones-weekly-return.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/room-occupancy-count.csv"
      },
      {
        "evidence_group": "external",
        "path": "data/external-qualification/canonical/tetouan-zone1-power.csv"
      }
    ],
    "dataset_sha256": {
      "data/examples/flat_spike.csv": "9a429b08d1abb3f2b53afde333248fb0ad7b2685f44608633c4b666b1b8c39be",
      "data/examples/sine_noise.csv": "e555b47912504c4405806c97f6d50ff408ef9201e0ef1904de7704ccecb4362e",
      "data/examples/trend.csv": "1cb13a9c80b2a9944b1eb13c18472972e695895b409bb217171f56166d420746",
      "data/external-qualification/canonical/appliances-energy.csv": "a7af25a1bebf2cbb0a017b3ab34e96904a61eefba59beae4cde011e64eab9402",
      "data/external-qualification/canonical/beijing-pm25.csv": "d060d68f6ca94364d7e07a4961075f0ea660616aa543c59a20133319417db18d",
      "data/external-qualification/canonical/dow-jones-weekly-return.csv": "c2d6c84ba8cac728b3e2f83288fc202ec2b6144dc868b3798f037392c5704f67",
      "data/external-qualification/canonical/fan-vibration-x.csv": "f04492df927bf24f41019990655451ecb7e997036bcc0a1a15db77b12eb54be4",
      "data/external-qualification/canonical/metro-traffic.csv": "23ce44d2d08325fb23bf4e8c04960c669281879b79e9cb2b8675d90e55294fde",
      "data/external-qualification/canonical/room-occupancy-count.csv": "cb5c023bae304933ecd15e9c8204b3832e7f35d3ef8c695ab7c7450d0242672a",
      "data/external-qualification/canonical/seoul-bike-demand.csv": "717730a0fd79b34d265781450bc0e12758e0758bb100f0bfd6784f14aacd058d",
      "data/external-qualification/canonical/tetouan-zone1-power.csv": "fc2f9ba9cf34689c7abbc253565f795f3ce46c369834cccdc80e35224a2a9cf1"
    },
    "dependency_versions": {
      "gorillacompression": "1.0.2",
      "lasagna-v2": "0.2.2",
      "project": {
        "name": "lasagna-v2",
        "version": "0.3.0"
      },
      "stdlib": "3.12.3"
    },
    "dirty_tree": true,
    "execution_order": [
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "trend.csv",
        "dataset_path": "data/examples/trend.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "trend.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "sine_noise.csv",
        "dataset_path": "data/examples/sine_noise.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "sine_noise.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "flat_spike.csv",
        "dataset_path": "data/examples/flat_spike.csv",
        "evidence_group": "internal",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "flat_spike.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "appliances-energy.csv",
        "dataset_path": "data/external-qualification/canonical/appliances-energy.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "appliances-energy.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "metro-traffic.csv",
        "dataset_path": "data/external-qualification/canonical/metro-traffic.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "metro-traffic.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "beijing-pm25.csv",
        "dataset_path": "data/external-qualification/canonical/beijing-pm25.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "beijing-pm25.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "seoul-bike-demand.csv",
        "dataset_path": "data/external-qualification/canonical/seoul-bike-demand.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "seoul-bike-demand.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "fan-vibration-x.csv",
        "dataset_path": "data/external-qualification/canonical/fan-vibration-x.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "fan-vibration-x.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "dow-jones-weekly-return.csv",
        "dataset_path": "data/external-qualification/canonical/dow-jones-weekly-return.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "dow-jones-weekly-return.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "room-occupancy-count.csv",
        "dataset_path": "data/external-qualification/canonical/room-occupancy-count.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "room-occupancy-count.csv:A4:cq=4"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=0.0625"
      },
      {
        "C_Q": 0.0625,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=0.0625"
      },
      {
        "C_Q": 0.125,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=0.125"
      },
      {
        "C_Q": 0.125,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=0.125"
      },
      {
        "C_Q": 0.25,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=0.25"
      },
      {
        "C_Q": 0.25,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=0.25"
      },
      {
        "C_Q": 0.5,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=0.5"
      },
      {
        "C_Q": 0.5,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=0.5"
      },
      {
        "C_Q": 1.0,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=1"
      },
      {
        "C_Q": 1.0,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=1"
      },
      {
        "C_Q": 2.0,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=2"
      },
      {
        "C_Q": 2.0,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=2"
      },
      {
        "C_Q": 4.0,
        "architecture": "A0",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A0:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A1",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A1:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A2",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A2:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A3",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A3:cq=4"
      },
      {
        "C_Q": 4.0,
        "architecture": "A4",
        "dataset": "tetouan-zone1-power.csv",
        "dataset_path": "data/external-qualification/canonical/tetouan-zone1-power.csv",
        "evidence_group": "external",
        "operations": [
          "canonical_v2_encode",
          "compact_encode",
          "untimed_equivalence",
          "compact_encode_warmup",
          "compact_encode_timed",
          "compact_decode_warmup",
          "compact_decode_timed"
        ],
        "point_id": "tetouan-zone1-power.csv:A4:cq=4"
      }
    ],
    "frozen_controls": {
      "C_Q": [
        0.0625,
        0.125,
        0.25,
        0.5,
        1.0,
        2.0,
        4.0
      ],
      "Q_MIN": 1e-06,
      "repetitions": 3,
      "residual_coding": "varint",
      "timing_statistic": "median wall-clock time",
      "warmup": 1,
      "wire_formats": [
        "canonical V2",
        "experimental compact V3"
      ]
    },
    "implementation_commit": "eb65daecd1cf6a2fac7a0cb32ba5103a30a712f0",
    "machine": "x86_64",
    "platform": "Linux-6.8.0-146-generic-x86_64-with-glibc2.39",
    "precorpus_tests_passed": true,
    "projection25_identity": {
      "implementation_path": "tools/analyze_segment_byte_anatomy.py",
      "implementation_sha256": "5987ad85fc760ac3ddb04e938e7984b4b27bdbcb8b38bc8d53c1844a52487e95",
      "protocol_path": "docs/segment-byte-anatomy-protocol.md",
      "protocol_sha256": "6f31719819763052c0c2a17f2a892d673358ed7004978ab70bc19c921bb1439c"
    },
    "protected_sha256": {
      "docs/compact-wire-layout-protocol.md": "6b2f1b2f469abf11a0d377d00806d87acca1cd9e2f4e364c691243269e547132",
      "docs/local-model-value-matched.csv": "b27d3d1c171a0edbbd2984798623ee74295e59555b64217142f9d1c7b50a6ae4",
      "docs/local-model-value-protocol.md": "75d29c40f653e8af43e798e6801eea6f1cbf1d333a275ad24815ccb2463cbbd1",
      "docs/local-model-value-provenance.json": "51b095f449a74936b0584bc46ee7f29d7f1ce48d1216636f949e4eb6d5abf383",
      "docs/local-model-value-results.csv": "d18d01b3994233bef4f8d84915778f84c94c26225c8fc76a76e5d1325b6a40a7",
      "docs/local-model-value-study.md": "c3abf9d54ee9be98476e4a1340ee870014d572769a2dfa92d6a03be94df89109",
      "docs/local-model-value-summary.csv": "87583353bb503290b90f4179f2abf897d84b186e871e227d663f37552fbd9f0a",
      "docs/segment-byte-anatomy-protocol.md": "6f31719819763052c0c2a17f2a892d673358ed7004978ab70bc19c921bb1439c",
      "docs/segment-byte-anatomy-results.csv": "6600d896e0d461dc69e18cd05eb9c24a9c161b6e6a8ff3b23de077568ed331bd",
      "docs/segment-byte-anatomy-study.md": "8cc7478f393009ad8cdb5eebccecb8515621cba3645650752c5bff99adb7739b",
      "docs/segment-byte-anatomy-summary.csv": "7e954986723809ef5965313b33e179b5eaf523d059e67abc9f5081569c64bec3",
      "lasagna2/__init__.py": "53bd10d0e579abb9e60e989ff3e4b5358360b7ffc19d92f4afe372278123fa0b",
      "lasagna2/core.py": "b9db63d5b4b37117e9eb2f55b21c0d75cabddd0ed3c195b6d4468981821c2a48",
      "tools/analyze_segment_byte_anatomy.py": "5987ad85fc760ac3ddb04e938e7984b4b27bdbcb8b38bc8d53c1844a52487e95",
      "tools/benchmark_local_model_value.py": "f722c304982db953e721193ac87b0571743c18640db1ca1da2dc53f65a04db90"
    },
    "protocol_path": "docs/compact-wire-layout-protocol.md",
    "protocol_sha256": "6b2f1b2f469abf11a0d377d00806d87acca1cd9e2f4e364c691243269e547132",
    "python_executable": "/home/baltimora/Progetti/giadaware/lasagna-v2/.venv/bin/python",
    "python_version": "3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]",
    "repetitions": 3,
    "schema_version": 26,
    "serialized_context": "{\"sampling\":{\"dt\":1.0,\"t0\":\"1970-01-01T00:00:00Z\"},\"unit\":\"local-model-value\"}",
    "timeseries_context": {
      "dt": 1.0,
      "t0": "1970-01-01T00:00:00Z",
      "unit": "local-model-value"
    },
    "v2_encoder_source_sha256": "b9db63d5b4b37117e9eb2f55b21c0d75cabddd0ed3c195b6d4468981821c2a48",
    "warmup": 1,
    "working_directory": "/home/baltimora/Progetti/giadaware/lasagna-v2"
  },
  "public_compatibility": {
    "public_decoder_rejects_v3": true,
    "public_default_v2": true,
    "v1_fixture_byte_identical": true,
    "v2_fixture_byte_identical": true
  },
  "question": "Does compact wire preserve V2 semantics while materially reducing actual serialized bytes?",
  "reporting_repair": {
    "command": ".venv/bin/python tools/benchmark_compact_wire.py --mode recover",
    "command_line": [
      ".venv/bin/python",
      "tools/benchmark_compact_wire.py",
      "--mode",
      "recover"
    ],
    "input_sha256": {
      "equivalence": "8045bb32901e1d7efe2a2cf04331a0f659d4b1f3d48ad2619f12f4bcab5bdc80",
      "provenance": "027deafd9e1beca3fe418711bf5e52b65ff255bd248ab41a3ec4324af5cd4591",
      "results": "bcacc6f1d8364998ac4758d9cbf94a1f5232a47b14132a49f3c12502b9d73d78",
      "summary": "e8b8981fb2d36238594958b2ef929a50076b723d585eba2f8b27b0efb49a8a0d"
    },
    "mode": "report-only recovery; canonical public compatibility fixtures only",
    "reporting_source_sha256": "cdbc7fbe3690bdf7fb75c1ed939732d415930b92e492923bf1ba57e714c38d7f"
  },
  "schema_version": 26,
  "scope": "Wire-layout validation; no codec-superiority claim or public format promotion.",
  "summary": [
    {
      "architecture": "A0",
      "dataset": "appliances-energy.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0011557208180493772,
      "median_compact_structural_fraction": 0.007193882684374686,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0011557208180493772,
      "median_v2_structural_fraction": 0.008341289382443093,
      "min_total_reduction_fraction": 0.0011392342364654473,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "appliances-energy.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.2124473141422294,
      "median_compact_structural_fraction": 0.2509299324375617,
      "median_total_byte_reduction": 7107,
      "median_total_reduction_fraction": 0.2124473141422294,
      "median_v2_structural_fraction": 0.41006785639554,
      "min_total_reduction_fraction": 0.21118473835913587,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "appliances-energy.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.22846979344154483,
      "median_compact_structural_fraction": 0.23691129843012915,
      "median_total_byte_reduction": 7591,
      "median_total_reduction_fraction": 0.22619794936179116,
      "median_v2_structural_fraction": 0.41006785639554,
      "min_total_reduction_fraction": 0.2233282515768391,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "appliances-energy.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3019040527603446,
      "median_compact_structural_fraction": 0.39857987444383497,
      "median_total_byte_reduction": 14191,
      "median_total_reduction_fraction": 0.3019040527603446,
      "median_v2_structural_fraction": 0.5801510477608764,
      "min_total_reduction_fraction": 0.30129511677282383,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "appliances-energy.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.32913519838315075,
      "median_compact_structural_fraction": 0.37622479297047856,
      "median_total_byte_reduction": 15367,
      "median_total_reduction_fraction": 0.3266029723991507,
      "median_v2_structural_fraction": 0.5801510477608764,
      "min_total_reduction_fraction": 0.3190086161046697,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "beijing-pm25.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0006704562017199045,
      "median_compact_structural_fraction": 0.004171285222565778,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0006704562017199045,
      "median_v2_structural_fraction": 0.004838944760239032,
      "min_total_reduction_fraction": 0.0006655670341754183,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "beijing-pm25.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21264954897241894,
      "median_compact_structural_fraction": 0.24927982407916438,
      "median_total_byte_reduction": 12282,
      "median_total_reduction_fraction": 0.21264954897241894,
      "median_v2_structural_fraction": 0.40892013089322504,
      "min_total_reduction_fraction": 0.2125170868444275,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "beijing-pm25.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.2241459909621345,
      "median_compact_structural_fraction": 0.23958124512751977,
      "median_total_byte_reduction": 12862,
      "median_total_reduction_fraction": 0.2225873400207541,
      "median_v2_structural_fraction": 0.40892013089322504,
      "min_total_reduction_fraction": 0.22165278667520816,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "beijing-pm25.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3021955694565873,
      "median_compact_structural_fraction": 0.3975612338533211,
      "median_total_byte_reduction": 24541,
      "median_total_reduction_fraction": 0.3021955694565873,
      "median_v2_structural_fraction": 0.5796155598517406,
      "min_total_reduction_fraction": 0.30208025603151156,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "beijing-pm25.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3210604735928284,
      "median_compact_structural_fraction": 0.3835945399393327,
      "median_total_byte_reduction": 25825,
      "median_total_reduction_fraction": 0.3180066248814787,
      "median_v2_structural_fraction": 0.5796155598517406,
      "min_total_reduction_fraction": 0.31593788865766115,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "dow-jones-weekly-return.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.12041884816753923,
      "median_compact_structural_fraction": 0.8511904761904762,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.12041884816753923,
      "median_v2_structural_fraction": 0.8691099476439791,
      "min_total_reduction_fraction": 0.12041884816753923,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "dow-jones-weekly-return.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.12041884816753923,
      "median_compact_structural_fraction": 0.8511904761904762,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.12041884816753923,
      "median_v2_structural_fraction": 0.8691099476439791,
      "min_total_reduction_fraction": 0.12041884816753923,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "dow-jones-weekly-return.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.1413612565445026,
      "median_compact_structural_fraction": 0.8511904761904762,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.12041884816753923,
      "median_v2_structural_fraction": 0.8691099476439791,
      "min_total_reduction_fraction": 0.12041884816753923,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "dow-jones-weekly-return.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.12041884816753923,
      "median_compact_structural_fraction": 0.8511904761904762,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.12041884816753923,
      "median_v2_structural_fraction": 0.8691099476439791,
      "min_total_reduction_fraction": 0.12041884816753923,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "dow-jones-weekly-return.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.1413612565445026,
      "median_compact_structural_fraction": 0.8511904761904762,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.12041884816753923,
      "median_v2_structural_fraction": 0.8691099476439791,
      "min_total_reduction_fraction": 0.12041884816753923,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "fan-vibration-x.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0001501638744890732,
      "median_compact_structural_fraction": 0.000933767785664379,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0001501638744890732,
      "median_v2_structural_fraction": 0.0010837914419649269,
      "min_total_reduction_fraction": 0.00014791852904671998,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "fan-vibration-x.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21288217213908012,
      "median_compact_structural_fraction": 0.24753975006516404,
      "median_total_byte_reduction": 54993,
      "median_total_reduction_fraction": 0.21288217213908012,
      "median_v2_structural_fraction": 0.407725122519607,
      "min_total_reduction_fraction": 0.21281050101968557,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "fan-vibration-x.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.23070461355032013,
      "median_compact_structural_fraction": 0.23081950400426318,
      "median_total_byte_reduction": 59413,
      "median_total_reduction_fraction": 0.22999233526629148,
      "median_v2_structural_fraction": 0.407725122519607,
      "min_total_reduction_fraction": 0.22567221263055204,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "fan-vibration-x.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.18771816743539738,
      "median_compact_structural_fraction": 0.21163279607568325,
      "median_total_byte_reduction": 44850,
      "median_total_reduction_fraction": 0.18771816743539738,
      "median_v2_structural_fraction": 0.3596236428625242,
      "min_total_reduction_fraction": 0.18766711160021254,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "fan-vibration-x.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.2030034906789664,
      "median_compact_structural_fraction": 0.19740652146544127,
      "median_total_byte_reduction": 48290,
      "median_total_reduction_fraction": 0.20211617180502428,
      "median_v2_structural_fraction": 0.3596236428625242,
      "min_total_reduction_fraction": 0.19943747331765183,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "flat_spike.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.04935622317596566,
      "median_compact_structural_fraction": 0.3227990970654628,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.04935622317596566,
      "median_v2_structural_fraction": 0.3562231759656652,
      "min_total_reduction_fraction": 0.04925053533190582,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "flat_spike.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.17912772585669778,
      "median_compact_structural_fraction": 0.4307400379506641,
      "median_total_byte_reduction": 115,
      "median_total_reduction_fraction": 0.17912772585669778,
      "median_v2_structural_fraction": 0.5327102803738317,
      "min_total_reduction_fraction": 0.17912772585669778,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "flat_spike.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.21028037383177567,
      "median_compact_structural_fraction": 0.41291585127201563,
      "median_total_byte_reduction": 131,
      "median_total_reduction_fraction": 0.2040498442367601,
      "median_v2_structural_fraction": 0.5327102803738317,
      "min_total_reduction_fraction": 0.18535825545171336,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "flat_spike.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.15384615384615385,
      "median_compact_structural_fraction": 0.40711462450592883,
      "median_total_byte_reduction": 92,
      "median_total_reduction_fraction": 0.15384615384615385,
      "median_v2_structural_fraction": 0.4983277591973244,
      "min_total_reduction_fraction": 0.15384615384615385,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "flat_spike.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.16722408026755853,
      "median_compact_structural_fraction": 0.40239043824701193,
      "median_total_byte_reduction": 96,
      "median_total_reduction_fraction": 0.1605351170568562,
      "median_v2_structural_fraction": 0.4983277591973244,
      "min_total_reduction_fraction": 0.15384615384615385,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "metro-traffic.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0004755013438081379,
      "median_compact_structural_fraction": 0.0029577843506318905,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0004755013438081379,
      "median_v2_structural_fraction": 0.0034318792640066157,
      "min_total_reduction_fraction": 0.0004755013438081379,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "metro-traffic.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21278005447719073,
      "median_compact_structural_fraction": 0.24869077306733167,
      "median_total_byte_reduction": 17342,
      "median_total_reduction_fraction": 0.21278005447719073,
      "median_v2_structural_fraction": 0.4085543913032809,
      "min_total_reduction_fraction": 0.21278005447719073,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "metro-traffic.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.23393290962184976,
      "median_compact_structural_fraction": 0.23001725129384704,
      "median_total_byte_reduction": 18898,
      "median_total_reduction_fraction": 0.2318716105126255,
      "median_v2_structural_fraction": 0.4085543913032809,
      "min_total_reduction_fraction": 0.21793330225025154,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "metro-traffic.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3023623008880437,
      "median_compact_structural_fraction": 0.3972465707176172,
      "median_total_byte_reduction": 34661,
      "median_total_reduction_fraction": 0.3023623008880437,
      "median_v2_structural_fraction": 0.5794964844635971,
      "min_total_reduction_fraction": 0.3023623008880437,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "metro-traffic.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.33345255334368507,
      "median_compact_structural_fraction": 0.3704501821886142,
      "median_total_byte_reduction": 38065,
      "median_total_reduction_fraction": 0.33205680688103,
      "median_v2_structural_fraction": 0.5794964844635971,
      "min_total_reduction_fraction": 0.31485423172880644,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "room-occupancy-count.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.002234094220495364,
      "median_compact_structural_fraction": 0.013921339563862928,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.002234094220495364,
      "median_v2_structural_fraction": 0.016124332200097135,
      "min_total_reduction_fraction": 0.002234094220495364,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "room-occupancy-count.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21203687597843102,
      "median_compact_structural_fraction": 0.25467255334805006,
      "median_total_byte_reduction": 3657,
      "median_total_reduction_fraction": 0.21203687597843102,
      "median_v2_structural_fraction": 0.41270945671711023,
      "min_total_reduction_fraction": 0.21193856853086057,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "room-occupancy-count.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.24891285440946254,
      "median_compact_structural_fraction": 0.2180793577273429,
      "median_total_byte_reduction": 4293,
      "median_total_reduction_fraction": 0.24891285440946254,
      "median_v2_structural_fraction": 0.41270945671711023,
      "min_total_reduction_fraction": 0.2485813549507817,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "room-occupancy-count.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.1336141166218866,
      "median_compact_structural_fraction": 0.15103511859860866,
      "median_total_byte_reduction": 1840,
      "median_total_reduction_fraction": 0.1336141166218866,
      "median_v2_structural_fraction": 0.2644688112700603,
      "min_total_reduction_fraction": 0.1335947142960865,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "room-occupancy-count.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.1568513542952582,
      "median_compact_structural_fraction": 0.12763758504866074,
      "median_total_byte_reduction": 2160,
      "median_total_reduction_fraction": 0.1568513542952582,
      "median_v2_structural_fraction": 0.2644688112700603,
      "min_total_reduction_fraction": 0.1564132327336042,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "seoul-bike-demand.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0025767421017253156,
      "median_compact_structural_fraction": 0.01606200157250365,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0025767421017253156,
      "median_v2_structural_fraction": 0.018597356038539098,
      "min_total_reduction_fraction": 0.00257184390025722,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "seoul-bike-demand.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21133467471495637,
      "median_compact_structural_fraction": 0.25503869376647675,
      "median_total_byte_reduction": 3151,
      "median_total_reduction_fraction": 0.21133467471495637,
      "median_v2_structural_fraction": 0.4124748490945674,
      "min_total_reduction_fraction": 0.211306330472103,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "seoul-bike-demand.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.2266264252179745,
      "median_compact_structural_fraction": 0.24214897482481185,
      "median_total_byte_reduction": 3351,
      "median_total_reduction_fraction": 0.22474849094567406,
      "median_v2_structural_fraction": 0.4124748490945674,
      "min_total_reduction_fraction": 0.2204560697518444,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "seoul-bike-demand.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.30098385710192,
      "median_compact_structural_fraction": 0.4014758130636786,
      "median_total_byte_reduction": 6302,
      "median_total_reduction_fraction": 0.30098385710192,
      "median_v2_structural_fraction": 0.5816219314165632,
      "min_total_reduction_fraction": 0.3009407382646483,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "seoul-bike-demand.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3283026076989206,
      "median_compact_structural_fraction": 0.3781942078364566,
      "median_total_byte_reduction": 6850,
      "median_total_reduction_fraction": 0.32715636641513035,
      "median_v2_structural_fraction": 0.5816219314165632,
      "min_total_reduction_fraction": 0.3143566720794727,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "sine_noise.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.04935622317596566,
      "median_compact_structural_fraction": 0.3227990970654628,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.04935622317596566,
      "median_v2_structural_fraction": 0.3562231759656652,
      "min_total_reduction_fraction": 0.04935622317596566,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "sine_noise.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.17912772585669778,
      "median_compact_structural_fraction": 0.4307400379506641,
      "median_total_byte_reduction": 115,
      "median_total_reduction_fraction": 0.17912772585669778,
      "median_v2_structural_fraction": 0.5327102803738317,
      "min_total_reduction_fraction": 0.17912772585669778,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "sine_noise.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.2040498442367601,
      "median_compact_structural_fraction": 0.42196531791907516,
      "median_total_byte_reduction": 123,
      "median_total_reduction_fraction": 0.19158878504672894,
      "median_v2_structural_fraction": 0.5327102803738317,
      "min_total_reduction_fraction": 0.17912772585669778,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "sine_noise.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.2011661807580175,
      "median_compact_structural_fraction": 0.45255474452554745,
      "median_total_byte_reduction": 138,
      "median_total_reduction_fraction": 0.2011661807580175,
      "median_v2_structural_fraction": 0.5626822157434402,
      "min_total_reduction_fraction": 0.2011661807580175,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "sine_noise.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.22448979591836737,
      "median_compact_structural_fraction": 0.43609022556390975,
      "median_total_byte_reduction": 154,
      "median_total_reduction_fraction": 0.22448979591836737,
      "median_v2_structural_fraction": 0.5626822157434402,
      "min_total_reduction_fraction": 0.20699708454810495,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "tetouan-zone1-power.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.0004374120421436478,
      "median_compact_structural_fraction": 0.002720751916893396,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.0004374120421436478,
      "median_v2_structural_fraction": 0.0031569738693849607,
      "min_total_reduction_fraction": 0.0004374120421436478,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "tetouan-zone1-power.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.21266963217196921,
      "median_compact_structural_fraction": 0.24837604141273642,
      "median_total_byte_reduction": 18837,
      "median_total_reduction_fraction": 0.21266963217196921,
      "median_v2_structural_fraction": 0.4082236322171292,
      "min_total_reduction_fraction": 0.21266963217196921,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "tetouan-zone1-power.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.23728182085036242,
      "median_compact_structural_fraction": 0.22494787738987712,
      "median_total_byte_reduction": 20921,
      "median_total_reduction_fraction": 0.2360625014112494,
      "median_v2_structural_fraction": 0.4082236322171292,
      "min_total_reduction_fraction": 0.22188226793415677,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "tetouan-zone1-power.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.30233528609260896,
      "median_compact_structural_fraction": 0.3970737093954173,
      "median_total_byte_reduction": 37674,
      "median_total_reduction_fraction": 0.30233528609260896,
      "median_v2_structural_fraction": 0.5793596019581093,
      "min_total_reduction_fraction": 0.3023013223777121,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "tetouan-zone1-power.csv",
      "evidence_group": "external",
      "max_total_reduction_fraction": 0.3306476205761978,
      "median_compact_structural_fraction": 0.37445102157723886,
      "median_total_byte_reduction": 40818,
      "median_total_reduction_fraction": 0.32756600593852825,
      "median_v2_structural_fraction": 0.5793596019581093,
      "min_total_reduction_fraction": 0.31642725302945185,
      "point_count": 7
    },
    {
      "architecture": "A0",
      "dataset": "trend.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.06284153005464477,
      "median_compact_structural_fraction": 0.41690962099125367,
      "median_total_byte_reduction": 23,
      "median_total_reduction_fraction": 0.06284153005464477,
      "median_v2_structural_fraction": 0.453551912568306,
      "min_total_reduction_fraction": 0.06284153005464477,
      "point_count": 7
    },
    {
      "architecture": "A1",
      "dataset": "trend.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.18473895582329314,
      "median_compact_structural_fraction": 0.5073891625615764,
      "median_total_byte_reduction": 92,
      "median_total_reduction_fraction": 0.18473895582329314,
      "median_v2_structural_fraction": 0.5983935742971888,
      "min_total_reduction_fraction": 0.18473895582329314,
      "point_count": 7
    },
    {
      "architecture": "A2",
      "dataset": "trend.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.18473895582329314,
      "median_compact_structural_fraction": 0.5073891625615764,
      "median_total_byte_reduction": 92,
      "median_total_reduction_fraction": 0.18473895582329314,
      "median_v2_structural_fraction": 0.5983935742971888,
      "min_total_reduction_fraction": 0.18473895582329314,
      "point_count": 7
    },
    {
      "architecture": "A3",
      "dataset": "trend.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.1121951219512195,
      "median_compact_structural_fraction": 0.45054945054945056,
      "median_total_byte_reduction": 46,
      "median_total_reduction_fraction": 0.1121951219512195,
      "median_v2_structural_fraction": 0.5121951219512195,
      "min_total_reduction_fraction": 0.1121951219512195,
      "point_count": 7
    },
    {
      "architecture": "A4",
      "dataset": "trend.csv",
      "evidence_group": "internal",
      "max_total_reduction_fraction": 0.1121951219512195,
      "median_compact_structural_fraction": 0.45054945054945056,
      "median_total_byte_reduction": 46,
      "median_total_reduction_fraction": 0.1121951219512195,
      "median_v2_structural_fraction": 0.5121951219512195,
      "min_total_reduction_fraction": 0.1121951219512195,
      "point_count": 7
    }
  ]
}
```
