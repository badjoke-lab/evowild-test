#!/usr/bin/env bash
set -euo pipefail
work=${1:?Pass the scratch directory used for measurement}
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
export TRIAL_URL=http://127.0.0.1:4210/evowild-test/
for mode in base group color both; do
  export TRIAL_EVIDENCE=$root/public/ridge-surface/evidence/$mode
  mkdir -p "$TRIAL_EVIDENCE"
  if test "$mode" = base; then unset RIDGE_ACTORS; else export RIDGE_ACTORS=$work/variants/$mode.js; fi
  node scripts/ridge-surface/regression.mjs > "$work/regression-$mode.log" 2>&1
done
for mode in base both; do
  export TRIAL_EVIDENCE=$root/public/ridge-surface/evidence/$mode
  if test "$mode" = base; then unset RIDGE_ACTORS; else export RIDGE_ACTORS=$work/variants/$mode.js; fi
  node scripts/ridge-surface/record.mjs > "$work/record-$mode.log" 2>&1
done
