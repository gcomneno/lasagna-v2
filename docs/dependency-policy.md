# Dependency and supply-chain policy

Issue: #23 — `deps: define dependency update and constraint policy`

Status:

```text
RUNTIME DEPENDENCY POLICY = FROZEN
BUILD DEPENDENCY POLICY = FROZEN
DEV / TOOLING DEPENDENCY POLICY = FROZEN
CI ACTION REFERENCE POLICY = FROZEN
DEPENDENCY UPDATE POLICY = FROZEN

PRODUCTION_READINESS_GATE_16=PASS
```

## 1. Scope

This policy governs:

```text
project runtime dependencies
Python build dependencies
developer/test dependencies
benchmark and analysis tooling
requirements-dev.txt
GitHub Actions references
dependency updates
dependency validation
```

It does not redefine the package/runtime matrix from
`docs/release-versioning-policy.md`.

## 2. Runtime dependencies

The current Lasagna package has:

```text
project runtime dependencies = none
```

The authoritative declaration is:

```toml
[project]
dependencies = []
```

in `pyproject.toml`.

Therefore no runtime lockfile is required for the current package baseline.

Adding any runtime dependency is a production-policy change. Such a change must
be reviewed for:

```text
necessity
version constraint
license
security posture
maintenance status
runtime/platform compatibility
release impact
```

and must update this policy and the relevant production-readiness evidence.

## 3. Build dependency

The current build backend is:

```text
setuptools.build_meta
```

with:

```text
setuptools>=61.0
```

The build dependency intentionally uses a minimum-version constraint rather than
an exact pin.

This is accepted because build tooling is not part of the installed Lasagna
runtime and the repository currently does not claim hermetic or bit-for-bit
reproducible package builds.

A future claim of hermetic/reproducible package builds would require a stronger
build-tool locking policy and separate qualification.

## 4. Development and test dependencies

The primary developer dependency declaration is:

```text
pyproject.toml [project.optional-dependencies].dev
```

Current policy:

```text
black              minimum constraint
ruff               minimum constraint
pre-commit         minimum constraint
detect-secrets     minimum constraint
pytest             minimum constraint
gorillacompression exact pin
```

Minimum constraints are intentionally accepted for ordinary development and
test tooling.

They mean:

```text
minimum supported tool version
not a complete environment lock
not a bit-reproducibility guarantee
```

The project does not claim that two independently resolved development
environments will contain identical transitive dependency versions.

## 5. Benchmark and reproducibility dependencies

Dependencies that materially participate in frozen comparative evidence may
require exact versions.

Current example:

```text
gorillacompression==1.0.2
```

This dependency is exact-pinned because comparison results must not silently
change because an external codec implementation changed.

Changing such a pin requires explicit review of any affected benchmark or
qualification evidence.

## 6. requirements-dev.txt role

`requirements-dev.txt` is a broader development/tooling manifest.

It includes the core development dependencies plus analysis/reporting tools:

```text
pandas
matplotlib
```

Those analysis packages are not project runtime dependencies and are not part
of the preferred CI install path in `.github/workflows/ci.yml`, which first
installs:

```text
-e ".[dev]"
```

`requirements-dev.txt` remains:

```text
a supported developer/tooling installation source
a fallback CI installation source
the current pip-audit input
```

It is not a runtime dependency declaration.

The overlap between `pyproject.toml` dev dependencies and
`requirements-dev.txt` must not silently disagree on version constraints.

Additional entries in `requirements-dev.txt` are permitted when they are
tooling/analysis-only and are classified as such by this policy.

## 7. Locking and constraint policy

Current constraint strategy:

```text
runtime                 no dependencies
build tooling            minimum constraint
ordinary dev/test tools  minimum constraints
analysis tools            minimum constraints
reproducibility-critical dependencies
                         exact pin where required
```

The project intentionally does not maintain a complete hash-locked Python
dependency graph at this stage.

This means registry resolution remains part of the accepted supply-chain risk.

A lockfile must not be introduced merely for appearance. It becomes mandatory
only if the project adopts a stronger claim such as:

```text
hermetic development environments
bit-reproducible package builds
fully frozen transitive dependency resolution
```

## 8. Dependency update policy

Dependency changes are repository changes and require review.

For each added, removed or updated Python dependency:

```text
1. classify it as runtime, build, dev/test, benchmark or analysis tooling;
2. justify the version constraint;
3. review compatibility and security implications;
4. update every duplicate declaration that intentionally represents the same
   dependency;
5. run the relevant tests and pre-commit checks;
6. update benchmark/qualification evidence when a reproducibility-critical
   dependency changes;
7. update release notes when user-visible behavior, compatibility or
   qualification evidence is affected.
```

Runtime dependency additions require explicit production-readiness review.

Exact-pinned benchmark dependencies must not be upgraded as incidental cleanup.

## 9. GitHub Actions reference policy

The default policy for third-party and first-party GitHub Actions is:

```text
immutable full commit SHA
```

Human-readable version comments may accompany the SHA.

The current workflows contain SHA-pinned references for the principal checkout,
Python setup, harden-runner, dependency-review, CodeQL and Scorecard actions.

Current explicit exception:

```text
pypa/gh-action-pip-audit@v1.1.0
```

This tag-based reference is mutable and is therefore not represented as
equivalent to SHA pinning.

It is an accepted residual supply-chain risk for the present qualification.

Any new mutable Action reference requires explicit justification in this policy.
The preferred remediation for existing or future mutable references is a
reviewed update to an immutable full commit SHA.

## 10. Supply-chain controls

Current controls include:

```text
dependency review
CodeQL
pip-audit
OpenSSF Scorecard
harden-runner
scoped workflow permissions
SHA-pinned Actions except the documented pip-audit exception
zero project runtime dependencies
```

These controls reduce risk but do not establish a hermetic build environment or
eliminate normal package-registry and CI supply-chain risk.

## 11. Validation requirements

A dependency-policy change must keep the following coherent:

```text
pyproject.toml
requirements-dev.txt
.github/workflows/
docs/dependency-policy.md
docs/security-review.md
docs/production-readiness.md
```

At minimum, affected changes must pass:

```text
pre-commit
relevant pytest coverage
dependency-policy regression tests
```

Release publication remains governed by the release-blocking CI contract in
`docs/release-versioning-policy.md`.

## 12. Accepted residual risk

The present production qualification explicitly accepts:

```text
unlocked transitive build/dev/tooling dependency resolution
package-registry resolution
one documented mutable pip-audit Action tag
normal upstream dependency and CI service risk
```

These are policy decisions, not claims that the risks do not exist.

A security finding may require tightening the policy without waiting for a
normal dependency-update cycle.

## 13. Gate assessment

The policy now explicitly defines:

```text
runtime dependencies
dependency classes
version-constraint conventions
update ownership/process
duplicate-manifest consistency
reproducibility-critical exact pins
GitHub Actions pinning rules
accepted mutable-reference exception
supply-chain controls
validation requirements
accepted residual risk
```

Therefore:

```text
PRODUCTION_READINESS_GATE_16=PASS
```
