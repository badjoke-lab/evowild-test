#!/usr/bin/env bash
set -euo pipefail

BASE="${BLENDCAP_MODEL_BASE:-https://huggingface.co/Blendcap/sam-3d-body/resolve/main}"

files=(
  "model.ckpt"
  "model_config.yaml"
  "assets/mhr_model.pt"
)

mkdir -p artifacts/blendcap-gate0
out="artifacts/blendcap-gate0/model-access.txt"
: > "$out"

for p in "${files[@]}"; do
  url="$BASE/$p"
  echo "== $p ==" | tee -a "$out"
  code="$(curl -L -sS -o /dev/null -w '%{http_code}' --range 0-0 "$url" || true)"
  echo "http_code=$code" | tee -a "$out"
  if [[ "$code" != "200" && "$code" != "206" ]]; then
    echo "MODEL_ACCESS_FAIL $p" | tee -a "$out"
    exit 4
  fi
done

echo "MODEL_ACCESS_PASS" | tee -a "$out"
