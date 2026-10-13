#!/usr/bin/env bash
set -euo pipefail
# Runs ONLY in a new isolated GitHub Codespace. Never use trading VM.
cd "$(git rev-parse --show-toplevel)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  ca-certificates curl xz-utils \
  xvfb xauth x11vnc xdotool x11-utils scrot openbox \
  novnc websockify \
  libegl1 libgl1 libgl1-mesa-dri libglx-mesa0 libx11-6 libxi6 \
  libxrender1 libxfixes3 libxkbcommon0 libsm6 libfontconfig1 \
  libxext6 libxinerama1 libxxf86vm1 libxcursor1 libxrandr2 \
  libasound2t64 libdbus-1-3 libwayland-client0
MODEL=art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend
REFERENCE=art/s-creature/references/00_s_type_modeling_image_v1.png
echo "93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6  $REFERENCE" | sha256sum --check -
test -s "$MODEL"
if [[ ! -x /opt/evowild-blender/blender ]]; then
  curl -L --fail --retry 3 \
    https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz \
    -o /tmp/evowild-blender-4.3.2.tar.xz
  sudo mkdir -p /opt/evowild-blender
  sudo tar --strip-components=1 -xf /tmp/evowild-blender-4.3.2.tar.xz -C /opt/evowild-blender
fi
/opt/evowild-blender/blender --version | head -n 2
echo 'S source modeling workstation ready; unedited original is protected'
