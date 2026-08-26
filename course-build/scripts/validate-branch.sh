#!/usr/bin/env bash
# Validate a single learner branch state built from the delta store.
#
# Builds the requested start-of-module-N branch from base + deltas into a temp
# worktree, then runs the service suites that exist in that cumulative state and
# asserts the tree is clean after setup. Suites are detected by presence so the
# same script works for every module (tests only appear from M03 onward).
#
# Usage: course-build/scripts/validate-branch.sh <start-of-module-NN>
#
# Env:
#   SKIP_APP_SUITES=1   Only run the deterministic delta/assets checks (fast).
#   DISPATCH_ID=<id>    Staging namespace (default: ci-local).

set -euo pipefail

START_BRANCH="${1:?usage: validate-branch.sh <start-of-module-NN>}"
DISPATCH_ID="${DISPATCH_ID:-ci-local}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Building ${START_BRANCH} from delta store (dispatch=${DISPATCH_ID})"
# Map start-of-module-(N+1) -> module N so we can bound --to.
mod_num="${START_BRANCH##*-}"          # e.g. 04
mod_num="${mod_num#0}"                  # strip leading zero -> 4
target_module=$(( mod_num - 1 ))        # module whose end == this start branch

node course-build/scripts/build-branches.mjs --dispatch-id "$DISPATCH_ID" --from "$target_module" --to "$target_module"

STAGING_REF="regen/${DISPATCH_ID}/${START_BRANCH}"
if ! git rev-parse --verify --quiet "refs/heads/${STAGING_REF}" >/dev/null; then
  echo "ERROR: expected staging ref ${STAGING_REF} was not created" >&2
  exit 1
fi

WT="$(mktemp -d)"
cleanup() {
  git worktree remove --force "$WT" 2>/dev/null || true
  git worktree prune 2>/dev/null || true
  git branch -D "$STAGING_REF" 2>/dev/null || true
}
trap cleanup EXIT

git worktree add -q "$WT" "$STAGING_REF"
cd "$WT"

echo "==> Clean-tree assertion (nothing uncommitted in built state)"
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: built branch has uncommitted files:" >&2
  git status --porcelain >&2
  exit 1
fi

if [ "${SKIP_APP_SUITES:-0}" = "1" ]; then
  echo "==> SKIP_APP_SUITES=1: skipping build/test suites"
  exit 0
fi

echo "==> web (Astro) build"
if [ -f services/web/package.json ]; then
  ( cd services/web && npm ci --no-audit --no-fund && npm run build )
fi

echo "==> assets-svc (.NET) build + test"
if [ -d services/assets-svc ]; then
  ( cd services/assets-svc && dotnet build --nologo )
  if ls services/assets-svc/Tests/*.cs >/dev/null 2>&1 || [ -d services/assets-svc/Tests ]; then
    ( cd services/assets-svc && dotnet test --nologo )
  fi
fi

echo "==> Java services build (all on Java 21; audit/auth target Java 17 bytecode before module 06, Java 21 after)"
[ -f services/workforce-svc/pom.xml ] && ( cd services/workforce-svc && mvn -q -B -DskipTests=false test )
[ -f services/audit-svc/pom.xml ]     && ( cd services/audit-svc && mvn -q -B -DskipTests=false test )
[ -f services/auth-svc/pom.xml ]      && ( cd services/auth-svc && mvn -q -B -DskipTests=false test )

echo "==> Python services install + pytest"
for svc in reporting-svc notifications-svc; do
  if [ -f "services/$svc/pyproject.toml" ]; then
    # Early modules ship a tests/ dir containing only a README; real test files
    # (test_*.py / *_test.py) appear from M03 onward. Only run pytest when they exist,
    # otherwise just verify the service is installable.
    if ls "services/$svc"/tests/test_*.py "services/$svc"/tests/*_test.py >/dev/null 2>&1; then
      # Install the dev extra (pins pytest/pytest-asyncio) when declared, and guarantee
      # pytest is importable so `python -m pytest` never fails with "No module named pytest".
      pip install -e "services/$svc[dev]"
      python -c "import pytest" 2>/dev/null || pip install pytest pytest-asyncio
      ( cd "services/$svc" && python -m pytest -q )
    else
      pip install -e "services/$svc"
    fi
  fi
done

echo "==> Playwright e2e (if present in this state)"
if [ -f playwright.config.ts ]; then
  npm ci --no-audit --no-fund
  npx playwright install --with-deps chromium

  # playwright.config's webServer runs `npm run dev` (the whole stack) but only waits for
  # the web app on :4321. The slower backends -- the JVM services especially -- are often
  # still booting when specs start, so any spec that transitively needs them flakes as
  # "element not found" (e.g. the asset detail page fetches assets-svc AND workforce-svc,
  # and hides its content -- including the QR card -- if either call fails). Pre-start the
  # full stack ourselves, wait for every service's /health, then run Playwright reusing the
  # warm server (reuseExistingServer is true when CI is unset) so specs only run once the
  # whole stack is ready.
  npm run dev >/tmp/e2e-stack.log 2>&1 &
  STACK_PID=$!

  wait_health() {
    local name="$1" url="$2" mode="${3:-ok}" i
    for i in $(seq 1 120); do
      if [ "$mode" = "any" ]; then
        # "server responding at all" -- the web root can 5xx while backends warm up.
        curl -s -o /dev/null "$url" && { echo "  ready: $name"; return 0; }
      else
        curl -sf "$url" >/dev/null 2>&1 && { echo "  ready: $name"; return 0; }
      fi
      if ! kill -0 "$STACK_PID" 2>/dev/null; then echo "ERROR: dev stack exited before $name was ready" >&2; return 1; fi
      sleep 2
    done
    echo "ERROR: timed out waiting for $name ($url)" >&2; return 1
  }

  stack_ok=1
  wait_health "web"           "http://localhost:4321/"        "any" || stack_ok=0
  [ "$stack_ok" = 1 ] && { wait_health "assets-svc"    "http://localhost:5001/health" || stack_ok=0; }
  [ "$stack_ok" = 1 ] && { wait_health "workforce-svc" "http://localhost:5002/health" || stack_ok=0; }
  # reporting/notifications/audit/auth also start via `npm run dev`; the current specs only
  # need web + assets-svc + workforce-svc, so we don't gate on the rest (keeps this robust
  # for earlier modules whose specs never touch them).

  if [ "$stack_ok" != 1 ]; then
    echo "==== dev stack log (tail) ===="; tail -n 150 /tmp/e2e-stack.log || true
    kill "$STACK_PID" 2>/dev/null || true
    exit 1
  fi

  # Reuse the already-warm stack (CI unset -> reuseExistingServer true); keep CI-style retries.
  set +e
  env -u CI npx playwright test --retries=2
  e2e_rc=$?
  set -e
  kill "$STACK_PID" 2>/dev/null || true
  if [ "$e2e_rc" -ne 0 ]; then
    echo "ERROR: Playwright e2e failed (exit $e2e_rc)" >&2
    exit "$e2e_rc"
  fi
fi

echo "==> ${START_BRANCH}: all applicable suites passed"
