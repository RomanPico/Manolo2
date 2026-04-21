================================================================================
=== This is a guide for configuritng the project. Its based in the A2A server===
================================================================================
NGA AI A2A SERVER — PROJECT TOOLCHAIN & CONFIGURATION GUIDE
================================================================================

This document describes how pyproject.toml, .pre-commit-config.yaml, and
related config files orchestrate the entire development lifecycle: building,
testing, linting, formatting, type-checking, security scanning, versioning,
and task automation.

Reference files:
  - pyproject.toml              (all tool configuration)
  - .pre-commit-config.yaml     (git hook pipeline)
  - uv.lock                     (deterministic dependency lockfile)
  - .devcontainer/              (containerized dev environment)


================================================================================
TABLE OF CONTENTS
================================================================================

  1. Build System
  2. UV Package Manager
  3. Dependency Groups (PEP 735)
  4. Task Runner (Poe the Poet)
  5. Pre-Commit Hook Pipeline
  6. Pytest
  7. Coverage
  8. Ruff (Formatter + Fast Linter)
  9. Pylint (Deep Static Analysis)
  10. MyPy (Static Type Checking)
  11. Bandit (Security Scanner)
  12. Semantic Release (Automated Versioning)
  13. End-to-End Flow


================================================================================
1. BUILD SYSTEM
================================================================================

  [build-system]
  requires = ["uv_build>=0.9.6,<0.10.0"]
  build-backend = "uv_build"

The project uses uv's own build backend rather than setuptools, hatchling, or
flit. When you run uv build, it produces a wheel and sdist using pyproject.toml
metadata directly.

This is a newer approach (2024+). The advantage is that the same tool (uv)
handles dependency resolution, virtual environments, locking, AND building.
There is no separate build toolchain to maintain.


================================================================================
2. UV PACKAGE MANAGER
================================================================================

  [tool.uv]
  package = false          # This is an application, not a publishable library.
  prerelease = "allow"     # Permits pre-release versions (e.g. ddtrace==4.7.0rc2)

  [tool.uv.build-backend]
  module-root = "."
  source-exclude = ["nga_ai_a2a_server/playground"]
  default-groups = ["dev", "test"]

Key concepts:

  package = false vs true
  ─────────────────────────
  The server sets package = false because it's a deployable application, not
  something you pip install from a registry. By contrast, nga-ai-a2a-core sets
  package = true because it IS published to Artifactory and consumed by other
  projects.

  When package = false, uv doesn't try to build/install the project itself
  into the virtual environment. It only installs the dependencies.

  prerelease = "allow"
  ─────────────────────
  By default, uv refuses to resolve pre-release versions. This setting is
  needed because the project pins ddtrace to a release candidate (4.7.0rc2).

  source-exclude
  ──────────────
  Strips the playground/ directory from built artifacts. The playground is
  development-only scratch code that should never be shipped.

  default-groups
  ──────────────
  When you run uv sync with no arguments, it installs the "dev" and "test"
  groups automatically. This means a fresh uv sync gives you everything
  needed for development and testing.

  Local dependency overrides
  ──────────────────────────
  [tool.uv.sources]
  # nga-ai-a2a-core = { path = "../nga-ai-a2a-core", editable = true }

  This commented-out line is important: when working on a2a-core and a2a-server
  simultaneously, you uncomment it to point at your local checkout instead of
  the Artifactory-published version. This gives you live editable access to the
  library without publishing a new version.

  Lockfile (uv.lock)
  ──────────────────
  The uv.lock file pins every transitive dependency to an exact version with
  SHA-256 hashes. This guarantees that every developer, CI runner, and
  production container gets the exact same dependency tree.

  Commands:
    uv lock         Regenerate the lockfile from pyproject.toml
    uv sync         Install dependencies from the lockfile
    uv build        Build wheel + sdist


================================================================================
3. DEPENDENCY GROUPS (PEP 735)
================================================================================

  [dependency-groups]
  build = ["wheel-inspect==1.7.1"]
  dev   = ["ipykernel==7.1.0", "marimo==0.17.7", "poethepoet==0.37.0", ...]
  lint  = ["pre-commit-uv==4.1.4", "pre-commit==4.1.0", "prek==0.2.15"]
  test  = ["pytest==8.3.4", "pytest-cov==6.0.0", "syrupy==4.8.0", ...]
  versioning = ["python-semantic-release==10.5.3"]

PEP 735 (standardized in 2024) provides a way to declare groups of development
dependencies separate from the project's runtime dependencies. Unlike
[project.optional-dependencies] (extras), these are not installable by
consumers -- they are purely for contributors and CI.

  Group       Purpose                              When installed
  ─────────── ──────────────────────────────────── ─────────────────────────
  build       Wheel inspection/validation           CI artifact stage
  dev         Notebooks, task runner, uv itself      Local development
  lint        pre-commit and helpers                 Running formatters/linters
  test        pytest + all plugins                   Running tests
  versioning  python-semantic-release                CI release stage

You install specific groups with:
  uv sync --group test
  uv run --group lint pre-commit run

This keeps environments lean. A CI test runner never installs notebook tools.
A developer's machine never installs the versioning tool.

  Detailed test dependencies:

  Package               Purpose
  ───────────────────── ────────────────────────────────────────────────────
  pytest                Test framework
  pytest-asyncio        Async test support (async def test_...)
  pytest-cov            Coverage measurement integrated with pytest
  pytest-dotenv         Loads .env file before tests
  pytest-env            Injects environment variables from pyproject.toml
  pytest-lazy-fixtures  Deferred fixture evaluation for parameterized tests
  pytest-recording      VCR.py integration for HTTP cassette recording
  pytest-testmon        Only re-runs tests affected by code changes
  coverage              The coverage.py engine behind pytest-cov
  syrupy                Snapshot testing (like Jest snapshots for Python)
  polyfactory           Generates fake data from Pydantic models

  Detailed dev dependencies:

  Package               Purpose
  ───────────────────── ────────────────────────────────────────────────────
  ipykernel             Jupyter kernel for notebooks in VS Code/Cursor
  marimo                Reactive Python notebooks (alternative to Jupyter)
  poethepoet            Task runner (the "poe" command)
  uv                    Pinned version of uv itself for consistency


================================================================================
4. TASK RUNNER (POE THE POET)
================================================================================

  [tool.poe.tasks]
  build              = "uv build"
  main               = "uv run --no-sync --group dev python -m nga_ai_a2a_server"
  test               = "uv run --no-sync --group test pytest ./tests"
  test_not_integration = "uv run --no-sync --group test pytest -k 'not integration' ./tests"
  format             = "uv run --no-sync --group lint pre-commit run --all-files --verbose"
  format-files       = "uv run --no-sync --group lint prek run --verbose ruff-format ruff-check pylint mypy"
  export             = "uv export --locked --format requirements-txt -o requirements.txt"
  coverage           = "uv run --no-sync --group test coverage report --fail-under=100"

Poe the Poet (poethepoet) is a task runner defined entirely in pyproject.toml.
It replaces Makefiles with a declarative, cross-platform alternative.

  Usage:
    poe build                Build wheel + sdist
    poe main                 Start the server locally
    poe test                 Run full test suite
    poe test_not_integration Run tests excluding integration tests
    poe format               Run all pre-commit hooks on all files
    poe format-files         Run specific linters (ruff, pylint, mypy) via prek
    poe export               Generate a requirements.txt from the lockfile
    poe coverage             Check coverage meets 100% threshold

  The --no-sync flag
  ──────────────────
  Every poe task uses uv run --no-sync. This tells uv to run the command
  without first checking/syncing dependencies. It trusts that you already ran
  uv sync. This makes task execution faster since it skips the resolution
  step every time.

  prek
  ────
  The format-files task uses prek, a helper that runs specific pre-commit
  hooks on just the files you've changed (instead of all files). Useful for
  quick feedback during development.


================================================================================
5. PRE-COMMIT HOOK PIPELINE
================================================================================

Configured in .pre-commit-config.yaml, this defines what runs automatically
on every git commit (and can be run manually with poe format).

  Hook execution order (pre-commit stage):

  #   Hook               Source                         Purpose
  ─── ────────────────── ────────────────────────────── ────────────────────────
  1   trailing-whitespace pre-commit/pre-commit-hooks    Remove trailing spaces
  2   end-of-file-fixer  pre-commit/pre-commit-hooks    Ensure newline at EOF
  3   check-yaml         pre-commit/pre-commit-hooks    Validate YAML syntax
  4   gitleaks           gitleaks/gitleaks              Detect secrets in code
  5   bandit             PyCQA/bandit                   Security vulnerability scan
  6   ruff-format        astral-sh/ruff-pre-commit      Code formatting
  7   ruff-check         astral-sh/ruff-pre-commit      Fast linting (25+ rule sets)
  8   pylint             PyCQA/pylint                   Deep static analysis
  9   mypy               pre-commit/mirrors-mypy        Static type checking
  10  uv-sync            astral-sh/uv-pre-commit        Verify lockfile is in sync

  Commit-msg stage:

  #   Hook               Source                         Purpose
  ─── ────────────────── ────────────────────────────── ────────────────────────
  11  commitlint         alessandrojcm/commitlint-...   Enforce conventional commits

  The pylint and mypy hooks have their own additional_dependencies lists
  that mirror the project's runtime dependencies. This is because pre-commit
  runs hooks in isolated virtual environments, so the hooks need to install
  the project's dependencies to do proper type checking and import analysis.

  Ruff's --exit-non-zero-on-fix flag means that if ruff auto-fixes a file,
  the commit is still blocked. You must stage the fix and commit again. This
  prevents accidentally committing un-linted code.


================================================================================
6. PYTEST
================================================================================

  [tool.pytest.ini_options]
  addopts = [
      "-r=a",                              # Show summary of ALL test outcomes
      "--doctest-modules",                  # Run doctests in source code
      "--junitxml=pytest-report.xml",       # JUnit XML report for CI
      "--cov=.",                            # Measure coverage of everything
      "--cov-report=xml",                   # Coverage XML (for CI tools)
      "--cov-report=html",                  # Coverage HTML (for local browsing)
      "--cov-report=term-missing:skip-covered",  # Terminal output, skip 100% files
      "--cov-fail-under=100",              # FAIL if coverage < 100%
      "--disable-warnings",                # Suppress pytest warnings
      "-vvv"                               # Maximum verbosity
  ]
  testpaths = ["tests"]
  python_classes = "!Test"

  Key behaviors:

  100% coverage enforcement
  ─────────────────────────
  The --cov-fail-under=100 flag means pytest will exit with a failure code if
  any measured line is not covered. This is an aggressive but effective policy.
  It's made practical by the coverage omit list (see section 7).

  Doctest modules
  ───────────────
  The --doctest-modules flag means any Python docstring containing >>> examples
  is executed as a test. For example:

    def add(a: int, b: int) -> int:
        """
        >>> add(1, 2)
        3
        """
        return a + b

  This docstring IS a test. If the function changes and the example breaks,
  the test suite catches it.

  python_classes = "!Test"
  ─────────────────────────
  The ! prefix means "NOT". Pytest normally collects classes starting with
  "Test" as test suites. This setting disables that behavior. Tests in this
  project use plain functions (def test_something), not test classes.

  This is important because Pydantic models or other classes that happen to
  start with "Test" (e.g., TestConfig) would otherwise be incorrectly
  collected as test suites.

  Test markers
  ────────────
  markers = [
      "vcr: cassette recording of http requests",
      "regression: reflect bugs and/or defects fixed",
      "asyncio: marks tests as async",
      "integration: integration tests requiring live services",
  ]

  Markers let you selectively run subsets of tests:
    pytest -m "not integration"    # Skip tests that need live services
    pytest -m regression           # Only run regression tests
    pytest -m vcr                  # Only run cassette-recorded tests

  Environment variables for tests
  ───────────────────────────────
  [tool.pytest_env]
  DB_USERNAME = { value = "test-user", skip_if_set = true }
  JWT_VALIDATION_ENABLED = { value = "False", skip_if_set = true }
  ...

  The pytest-env plugin injects fake environment variables before tests run.
  The skip_if_set = true pattern means:

    - Locally: uses fake values (no real credentials needed)
    - CI with secrets: real values take precedence
    - Integration tests: set real values to test against live services

  This single mechanism handles three different execution contexts without
  any test code changes.

  VCR / cassette recording (pytest-recording)
  ────────────────────────────────────────────
  Tests decorated with @pytest.mark.vcr record HTTP interactions to YAML
  cassette files on first run. On subsequent runs, the cassettes are replayed
  instead of making real HTTP calls. This makes tests:
    - Fast (no network latency)
    - Deterministic (same response every time)
    - Offline-capable (no network needed after first recording)

  The a2a-core project adds --record-mode=once to addopts, which means
  cassettes are recorded once and then always replayed. In CI, new cassettes
  are recorded; locally, they replay.

  Snapshot testing (syrupy)
  ─────────────────────────
  Syrupy provides snapshot testing similar to Jest's toMatchSnapshot(). On
  first run, it saves the output (e.g., a complex dict, API response, or
  serialized object) to a _snapshots_/ directory. On subsequent runs, it
  compares against the saved snapshot.

  To update snapshots after intentional changes:
    pytest --snapshot-update


================================================================================
7. COVERAGE
================================================================================

  [tool.coverage.run]
  relative_files = true
  omit = [
      "nga_ai_a2a_server/playground/*",
      "nga_ai_a2a_server/_init_.py",
      "nga_ai_a2a_server/certs/*",
      "nga_ai_a2a_server/_main_.py",
      "nga_ai_a2a_server/injections/*",
      "nga_ai_a2a_server/agents/base/agent.py",
      "nga_ai_a2a_server/agents/ai_assistant_agent/executor/*",
      "nga_ai_a2a_server/agents/ai_assistant_agent/agent.py",
      "nga_ai_a2a_server/agents/project_manager/agent.py",
      "nga_ai_a2a_server/agents/project_manager/agent_tools.py",
      "nga_ai_a2a_server/agents/project_manager/prompts.py",
      "nga_ai_a2a_server/agents/project_manager/skills/*",
      "nga_ai_a2a_server/settings.py",
      "nga_ai_a2a_server/server/uvicorn_server.py",
      "nga_ai_a2a_server/server/lifecycle/*",
      "nga_ai_a2a_server/server/routers/copilot/*",
      "nga_ai_a2a_server/server/routers/speech/*",
      "nga_ai_a2a_server/server/app.py",
      "nga_ai_a2a_server/utils/*",
  ]

  The 100% coverage requirement is made achievable by omitting files that
  are inherently difficult or impractical to unit test:

  Category                      Why omitted
  ───────────────────────────── ───────────────────────────────────────────
  _main_.py, settings.py      Entry points with env-dependent behavior
  injections/*                  DI container wiring (framework boilerplate)
  server/app.py, lifecycle/*    FastAPI app factory, startup/shutdown hooks
  server/uvicorn_server.py      Uvicorn server creation
  agents/*/agent.py             Agent orchestration (tested via integration)
  agents//executor/           LLM execution layer (mocked in unit tests)
  playground/*                  Development scratch code
  certs/*                       Certificate files
  utils/*                       Utility functions (presumably thin wrappers)

  [tool.coverage.report]
  exclude_lines = ["assert_never", "if TYPE_CHECKING:"]
  exclude_also = ["pragma: no cover", "@overload", "Protocol", "@pytest.mark.xfail"]

  Individual lines/blocks can also be excluded:
    - assert_never       — unreachable exhaustiveness checks
    - if TYPE_CHECKING:  — import blocks only used by type checkers
    - @overload          — function overload signatures (not real code)
    - Protocol           — structural typing definitions
    - pragma: no cover   — explicit opt-out for specific lines

  [tool.coverage.paths]
  source = ["nga_ai_a2a_server", "*/nga_ai_a2a_server"]

  This path mapping ensures coverage works correctly whether measured inside
  the container (absolute paths) or outside (relative paths). The * glob
  handles the prefix difference.


================================================================================
8. RUFF (FORMATTER + FAST LINTER)
================================================================================

  [tool.ruff]
  fix = true         # Auto-fix issues where possible
  preview = true     # Enable unstable/preview rules

Ruff is a Rust-based Python linter and formatter that replaces Black, isort,
flake8, and many flake8 plugins in a single tool. It's 10-100x faster than
the tools it replaces.

  Formatting (replaces Black):
  ────────────────────────────
  [tool.ruff.format]
  quote-style = "double"
  indent-style = "space"
  skip-magic-trailing-comma = false
  line-ending = "auto"

  This produces Black-compatible output: double quotes, 4-space indentation,
  respects trailing commas for multi-line expressions.

  Linting (replaces flake8 + plugins):
  ─────────────────────────────────────
  The extend-select list enables 25+ rule categories:

  Code     Name                        What it catches
  ──────── ─────────────────────────── ──────────────────────────────────────
  E        pycodestyle                 PEP 8 style violations
  UP       pyupgrade                   Old syntax that can be modernized
  B        flake8-bugbear              Common Python bugs and design issues
  A        flake8-builtins             Shadowing of Python builtins
  C4       flake8-comprehensions       Unnecessary list/dict/set patterns
  SIM      flake8-simplify             Overly complex code
  I        isort                       Import ordering
  T20      flake8-print                print() calls in production code
  EM       flake8-errmsg               Bad exception message patterns
  PT       flake8-pytest-style         Pytest best practices
  RET      flake8-return               Return statement issues
  TRY      tryceratops                 Exception handling anti-patterns
  PERF     Perflint                    Performance anti-patterns
  FURB     refurb                      Modernization suggestions
  ERA      eradicate                   Commented-out code detection
  ARG      flake8-unused-arguments     Unused function arguments
  FBT      flake8-boolean-trap         Boolean arguments in function sigs
  BLE      flake8-blind-except         Bare except clauses
  COM      flake8-commas               Missing trailing commas
  ICN      flake8-import-conventions   Non-standard import aliases
  PIE      flake8-pie                  Misc. code quality
  RSE      flake8-return               Unnecessary return None
  SLF      flake8-self                 Private member access
  TID      flake8-tidy-imports         Banned imports, relative imports
  PTH      flake8-use-pathlib          os.path -> pathlib suggestions
  LOG      flake8-logging              Logging best practices
  G        flake8-logging-format       Logging format string issues
  ISC      flake8-implicit-str-concat  Implicit string concatenation
  TD       flake8-todos                TODO comment format
  FIX      flake8-fixme                FIXME/TODO/XXX tracking
  RUF      ruff-specific               Ruff's own custom rules

  Intentionally ignored rules:

  Code     Reason
  ──────── ────────────────────────────────────────────────────────
  SIM117   Nested with statements needed for test patterns
  ISC001   Conflicts with ruff formatter
  COM812   Conflicts with ruff formatter
  E203     Conflicts with ruff formatter
  TD002    Team doesn't require author on TODO comments
  TD003    Team doesn't require links on TODO comments
  SLF001   Private member access allowed (team decision)
  PT001    Conflicts with parentheses style
  FIX002   TODOs allowed for tracking tech debt explicitly


================================================================================
9. PYLINT (DEEP STATIC ANALYSIS)
================================================================================

Pylint runs as a second linting layer on top of Ruff. While Ruff handles
style and common patterns with speed, Pylint performs deeper program analysis
that Ruff cannot (yet) replicate.

  [tool.pylint.main]
  fail-on = ["I"]            # Fail on informational messages
  fail-under = 10            # Require perfect score (10.0/10.0)
  jobs = 4                   # Parallel analysis across 4 cores

  Design constraints (enforced limits):
  ─────────────────────────────────────
  [tool.pylint.design]
  max-args = 5               # No function with > 5 parameters
  max-attributes = 5         # No class with > 5 attributes
  max-bool-expr = 5          # No expression with > 5 boolean operators
  max-branches = 8           # No function with > 8 if/elif/else branches
  max-complexity = 10        # McCabe cyclomatic complexity limit
  max-locals = 10            # No function with > 10 local variables
  max-parents = 7            # No class with > 7 parent classes
  max-public-methods = 11    # No class with > 11 public methods
  max-returns = 6            # No function with > 6 return statements
  max-statements = 30        # No function with > 30 statements

  [tool.pylint.format]
  max-line-length = 120      # Lines must be ≤ 120 characters
  max-module-lines = 310     # Files must be ≤ 310 lines

  These limits force code to stay small and focused. If you exceed them,
  you must refactor — split the function, extract a class, etc.

  Naming conventions:
  ───────────────────
  [tool.pylint.basic]
  argument-naming-style = "snake_case"
  function-naming-style = "snake_case"
  variable-naming-style = "snake_case"
  class-naming-style = "PascalCase"
  const-naming-style = "UPPER_CASE"
  module-naming-style = "snake_case"

  All names must be 2-30 characters (per the regex patterns). Single-letter
  names are only allowed for: i, j, k, ex, Run, _

  Extension plugins loaded (13):
  ──────────────────────────────
  Plugin                                     What it checks
  ────────────────────────────────────────── ──────────────────────────────
  bad_builtin                                Use of map() and filter()
  code_style                                 Modern Python idioms
  comparison_placement                       Constant on wrong side of ==
  consider_refactoring_into_while_condition  For loops that should be while
  dunder                                     Proper dunder method usage
  eq_without_hash                            _eq_ without _hash_
  for_any_all                                Loops replaceable with any/all
  mccabe                                     Cyclomatic complexity
  no_self_use                                Methods that should be functions
  overlapping_exceptions                     Redundant except clauses
  private_import                             Importing private modules
  redefined_loop_name                        Reusing loop variable names
  set_membership                             Using list where set is better

  Deliberately disabled checks:
  ─────────────────────────────
  Check                         Reason
  ───────────────────────────── ─────────────────────────────────────────────
  redefined-outer-name          Common in pytest fixtures
  missing-*-docstring           Team doesn't mandate docstrings
  import-error                  Handled by the build system
  invalid-name                  Some names don't match regex but are fine
  logging-fstring-interpolation Team uses f-strings in logging
  unused-import                 Delegated to Ruff (faster)
  too-few-public-methods        DI plugins/Pydantic models often have few
  missing-kwoa                  DI framework injects kwargs
  no-self-use                   Test methods don't use self
  duplicate-code                Test files have similar patterns by design
  protected-access              Needed for testing private members

  Delegation to Ruff:
  ──────────────────
  Some checks are explicitly disabled in pylint because Ruff handles them:
    - unused-import  → Ruff F401
    - unused-argument → Ruff ARG002 (in a2a-core)
  This avoids duplicate warnings and leverages Ruff's speed.


================================================================================
10. MYPY (STATIC TYPE CHECKING)
================================================================================

  [tool.mypy]
  strict = true                  # Strictest mode
  disallow_untyped_defs = true   # Every function must have type annotations
  check_untyped_defs = true      # Type-check functions even without annotations
  ignore_missing_imports = true  # Don't fail on third-party libs without stubs

  strict = true enables ALL of these checks simultaneously:
    - disallow_any_generics
    - disallow_subclassing_any
    - disallow_untyped_calls
    - disallow_untyped_decorators
    - disallow_untyped_defs
    - no_implicit_optional
    - no_implicit_reexport
    - strict_equality
    - warn_redundant_casts
    - warn_return_any
    - warn_unused_configs
    - warn_unused_ignores

  In practice this means:
    - Every function parameter and return type must be annotated
    - No implicit Any types
    - No untyped decorators
    - Strict equality checking (no comparing incompatible types)

  ignore_missing_imports = true is a practical compromise: many third-party
  libraries (dependency-injector, litellm, etc.) don't ship type stubs, and
  blocking on that would be impractical.

  The a2a-core project additionally loads the pydantic.mypy plugin, which
  gives mypy better understanding of Pydantic models (field types, validators,
  model_validate, etc.).


================================================================================
11. BANDIT (SECURITY SCANNER)
================================================================================

  [tool.bandit]
  exclude_dirs = ["tests", "examples"]

Bandit is a static security analysis tool for Python. It scans for common
security issues:

  - Hardcoded passwords or secret keys
  - Use of assert in production code (stripped by -O flag)
  - Shell injection via subprocess
  - Unsafe YAML/pickle loading
  - SQL injection patterns
  - Weak cryptographic algorithms
  - Binding to 0.0.0.0
  - Use of eval/exec

Tests and examples are excluded because they legitimately contain fake
secrets, test patterns, and demonstration code that would trigger false
positives.

Bandit runs as step 5 in the pre-commit pipeline, catching security issues
before code is even committed.


================================================================================
12. SEMANTIC RELEASE (AUTOMATED VERSIONING)
================================================================================

  [tool.semantic_release]
  commit_message = "chore(release): bump version and update changelog [skip ci]"
  version_source = "tag"
  tag_format = "{version}"
  version_toml = ["pyproject.toml:project.version"]

  [tool.semantic_release.commit_parser_options]
  allowed_tags = ["chore", "feat", "fix"]
  minor_tags = ["feat"]
  patch_tags = ["fix"]

  [tool.semantic_release.changelog]
  changelog_file = "CHANGELOG.md"
  exclude_commit_patterns = ["chore*", "Merge*"]

This system automates version bumping based on conventional commit messages:

  Commit prefix     Version bump       Example
  ───────────────── ────────────────── ─────────────────────────────
  fix: ...          Patch (x.y.Z)      1.26.36 → 1.26.37
  feat: ...         Minor (x.Y.0)      1.26.36 → 1.27.0
  chore: ...        No bump            (version unchanged)

  How it works:
  1. Developer merges a PR with conventional commit messages
  2. CI runs python-semantic-release
  3. It analyzes commits since the last tag
  4. Determines the appropriate version bump
  5. Updates version in pyproject.toml
  6. Generates/updates CHANGELOG.md
  7. Creates a git tag
  8. Commits with "chore(release): ..." message
  9. The [skip ci] suffix prevents the release commit from triggering CI again

  version_source = "tag" means the source of truth for the current version
  is the latest git tag, not the pyproject.toml value. The pyproject.toml
  version is updated to match, but tags are authoritative.

  Branch matching:
  [tool.semantic_release.branches.main]
  match = '(main|^[a-zA-Z0-9-_.\/]*$)'

  This regex matches "main" and essentially any other branch name. This means
  semantic-release runs on all branches, not just main. On feature branches,
  it can produce pre-release versions.

  IMPORTANT: If you manually commit without a conventional prefix (e.g.,
  "updated auth version"), semantic-release won't bump the version. The CI
  Artifactory check will then fail because it tries to publish a version that
  already exists. Always use feat:/fix:/chore: prefixes.


================================================================================
13. END-TO-END FLOW
================================================================================

  Here is the complete flow from code change to production deployment:

  ┌─────────────────────────────────────────────────────────────────────┐
  │  DEVELOPMENT                                                        │
  │                                                                     │
  │  1. Developer writes code                                           │
  │  2. poe test — runs pytest with 100% coverage check              │
  │  3. poe format — runs all pre-commit hooks                       │
  │  4. git add . && git commit -m "fix: update auth to 2.2.0"       │
  │                                                                     │
  │  On commit, pre-commit automatically runs:                          │
  │    ┌──────────────────────────────────────────────────────┐         │
  │    │  1. trailing-whitespace     (cleanup)                │         │
  │    │  2. end-of-file-fixer       (cleanup)                │         │
  │    │  3. check-yaml              (syntax)                 │         │
  │    │  4. gitleaks                (secrets detection)      │         │
  │    │  5. bandit                  (security scan)          │         │
  │    │  6. ruff-format             (formatting)             │         │
  │    │  7. ruff-check              (fast linting)           │         │
  │    │  8. pylint                  (deep analysis)          │         │
  │    │  9. mypy                    (type checking)          │         │
  │    │  10. uv-sync                (lockfile integrity)     │         │
  │    └──────────────────────────────────────────────────────┘         │
  │                                                                     │
  │  On commit message, commitlint verifies:                            │
  │    ✓ Message starts with feat:/fix:/chore:                         │
  │    ✓ Subject line follows conventional format                      │
  │                                                                     │
  │  5. git push → opens PR                                          │
  └─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  CI PIPELINE                                                        │
  │                                                                     │
  │  1. Validate version doesn't exist in Artifactory                  │
  │  2. Install dependencies from lockfile                             │
  │  3. Run full test suite (pytest + coverage)                        │
  │  4. Run linters (ruff, pylint, mypy, bandit)                       │
  │  5. Build wheel                                                    │
  │  6. Semantic-release analyzes commits, bumps version               │
  │  7. Publish to Artifactory                                         │
  │  8. Create git tag                                                 │
  └─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │  DEPLOYMENT                                                         │
  │                                                                     │
  │  Docker image built from Dockerfile:                               │
  │    - Base: python:3.12 + uv                                        │
  │    - Dependencies installed from lockfile (frozen)                  │
  │    - CMD: ddtrace-run python -m nga_ai_a2a_server                  │
  │    - Exposed on port 8082                                          │
  └─────────────────────────────────────────────────────────────────────┘


================================================================================
APPENDIX: DIFFERENCES BETWEEN A2A-SERVER AND A2A-CORE
================================================================================

  Aspect                   a2a-server              a2a-core
  ──────────────────────── ─────────────────────── ─────────────────────────
  package                  false (application)      true (library)
  Dependency pinning       == (exact pins)          >= (floor pins)
  Coverage omit list       Large (many app files)   Small (just certs, cassettes)
  pytest-env style         { value, skip_if_set }   Plain string values
  VCR record mode          (default)                --record-mode=once
  Pylint py-version        3.13                     3.10
  MyPy pydantic plugin     No                       Yes
  Additional ruff ignores  —                        UP040, UP042, UP046, UP047
                                                     (PEP 695 migration deferred)

  The dependency pinning difference is significant:
    - a2a-server pins to == because as a deployed app, reproducibility is
      paramount. You want the exact same versions in dev, CI, and production.
    - a2a-core uses >= because as a library, it should be compatible with a
      range of dependency versions. Consumers (like a2a-server) pin the
      actual resolved version via their own lockfile.