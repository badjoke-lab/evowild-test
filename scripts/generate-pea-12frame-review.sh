#!/usr/bin/env bash
set -euo pipefail

OUT="artifacts/pea-12frame"
rm -rf "$OUT"
mkdir -p "$OUT"

ffmpeg -hide_banner -version | head -n 1

make_candidate() {
  local morph="$1"
  local cols="$2"
  local rows="$3"
  local lower
  lower="$(echo "$morph" | tr '[:upper:]' '[:lower:]')"
  local src="public/concept/$lower-run-sheet.webp"
  local dir="$OUT/$morph"
  mkdir -p "$dir/base" "$dir/interp"

  local cell_w=$((768 / cols))
  local cell_h=$((512 / rows))

  for i in 0 1 2 3 4 5; do
    local col row
    if [[ "$morph" == "A" ]]; then
      col=$((i % 2))
      row=$((i / 2))
    else
      col=$((i % 3))
      row=$((i / 3))
    fi

    ffmpeg -hide_banner -loglevel error -y \
      -i "$src" \
      -vf "crop=$cell_w:$cell_h:$((col * cell_w)):$((row * cell_h)),format=rgba" \
      -frames:v 1 "$dir/base/$(printf '%02d' "$i").png"
  done

  {
    for i in 0 1 2 3 4 5; do
      printf "file '%s'\n" "$(realpath "$dir/base/$(printf '%02d' "$i").png")"
      printf "duration 0.100000\n"
    done
    printf "file '%s'\n" "$(realpath "$dir/base/00.png")"
  } > "$dir/concat.txt"

  ffmpeg -hide_banner -loglevel error -y \
    -f concat -safe 0 -i "$dir/concat.txt" \
    -vf "minterpolate=fps=20:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" \
    -frames:v 13 "$dir/interp/%02d.png"

  ffmpeg -hide_banner -loglevel error -y \
    -framerate 1 -start_number 1 -i "$dir/interp/%02d.png" \
    -vf "select='lt(n,12)',tile=4x3:padding=8:margin=8" \
    -frames:v 1 "$OUT/$lower-12frame-sheet.png"

  ffmpeg -hide_banner -loglevel error -y \
    -framerate 20 -start_number 1 -i "$dir/interp/%02d.png" \
    -vf "select='lt(n,12)',setpts=N/(20*TB)" \
    -frames:v 12 -c:v libvpx-vp9 -pix_fmt yuva420p \
    "$OUT/$lower-12frame-preview.webm"

  ffmpeg -hide_banner -loglevel error -y \
    -framerate 1 -start_number 0 -i "$dir/base/%02d.png" \
    -vf "tile=3x2:padding=8:margin=8" \
    -frames:v 1 "$OUT/$lower-6frame-source.png"
}

make_candidate P 3 2
make_candidate E 3 2
make_candidate A 2 3

cat > "$OUT/README.txt" <<'TXT'
PEA 12-frame optical-flow candidate.
Source:
- P/E: existing 3x2 six-frame sheets
- A: corrected 2x3 six-frame sheet
Method:
- crop existing six poses
- close LAND -> CONTACT cycle
- motion-compensated interpolation from 10 fps to 20 fps
- retain first 12 frames of the closed cycle
This is review-only. It must not replace production assets unless visual review passes.
TXT
