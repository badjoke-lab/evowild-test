#!/usr/bin/env bash
set -euo pipefail
# Web desktop allows browser-driven GUI inside Codespaces:
# Work Cloud Browser can interact with noVNC web UI, unlike native Blender.
# NEVER expose port 6080 publicly. Codespaces defaults to PRIVATE.
cd "$(git rev-parse --show-toplevel)"
mkdir -p /tmp/evowild-s-gui
export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
if ! xdpyinfo -display :99 >/dev/null 2>&1; then
  nohup Xvfb :99 -screen 0 1600x1000x24 +extension GLX +render -noreset -ac \
    > /tmp/evowild-s-gui/xvfb.log 2>&1 < /dev/null &
  for k in 1 2 3 4 5 6 7 8 9 10; do
    xdpyinfo -display :99 >/dev/null 2>&1 && break
    sleep 1
  done
fi
xdpyinfo -display :99 >/dev/null
if ! pgrep -x openbox >/dev/null; then
  nohup openbox > /tmp/evowild-s-gui/openbox.log 2>&1 < /dev/null &
fi
if ! pgrep -x x11vnc >/dev/null; then
  # Only localhost is accessible; GitHub's authenticated PRIVATE port forward
  # is the sole supported access to websockify on 6080.
  nohup x11vnc -display :99 -rfbport 5900 -localhost -nopw -forever -shared -quiet \
    > /tmp/evowild-s-gui/x11vnc.log 2>&1 < /dev/null &
fi
if ! curl -fsS http://127.0.0.1:6080/vnc.html >/dev/null 2>&1; then
  nohup websockify --web=/usr/share/novnc/ 6080 127.0.0.1:5900 \
    > /tmp/evowild-s-gui/websockify.log 2>&1 < /dev/null &
fi
MODEL="$PWD/art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend"
test -s "$MODEL"
# Save native Blender user preferences first, so the initial language/theme
# Quick Setup wizard never obscures the actual model when browser opens.
if [[ ! -s "$HOME/.config/blender/4.3/config/userpref.blend" ]]; then
  /opt/evowild-blender/blender -b --python-expr "import bpy; bpy.ops.wm.save_userpref()" \
    >> /tmp/evowild-s-gui/prefs.log 2>&1
fi
if ! pgrep -x blender >/dev/null; then
  # GUI application is real Blender, not a rendered web mockup.
  nohup /opt/evowild-blender/blender --disable-autoexec -W "$MODEL" \
    > /tmp/evowild-s-gui/blender-gui.log 2>&1 < /dev/null &
  echo $! > /tmp/evowild-s-gui/blender.pid
fi
for k in $(seq 1 45); do
  if DISPLAY=:99 xdotool search --onlyvisible --class Blender >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
# Frame the already-selected real Hunyuan mesh; navigation only, zero
# changes to vertices, topology, geometry or canonical illustration.
WIN="$(DISPLAY=:99 xdotool search --onlyvisible --class Blender | head -n 1)"
if [[ -n "$WIN" ]]; then
  DISPLAY=:99 xdotool windowactivate --sync "$WIN" || true
  DISPLAY=:99 xdotool mousemove --window "$WIN" 490 420 key --clearmodifiers KP_Decimal || true
  sleep 5
fi
echo '=== Real GUI process and browser access status ==='
echo "DISPLAY=$DISPLAY"
DISPLAY=:99 glxinfo -B 2>/dev/null | grep -E 'OpenGL renderer|OpenGL version' || true
DISPLAY=:99 xdotool search --onlyvisible --class Blender >/dev/null &&
  echo 'PASS: Real Blender GUI is running as a visible window'
curl -fsS http://127.0.0.1:6080/vnc.html >/dev/null &&
  echo 'PASS: Browser noVNC desktop serves port 6080 (Codespaces PRIVATE only)'
echo 'Open Codespaces forwarded port 6080 /vnc.html to edit the actual S model.'
echo 'You must use Save As under the experiment folder before making geometry changes.'
