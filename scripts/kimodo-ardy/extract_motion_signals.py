#!/usr/bin/env python3
"""Extract transferable locomotion signals from Kimodo/ARDY NPZ output.

The script deliberately analyzes root/contact timing rather than retargeting
humanoid joint rotations onto the EvoWild quadruped.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


def _scalar(data: dict[str, np.ndarray], key: str) -> float | None:
    if key not in data:
        return None
    arr = np.asarray(data[key])
    if arr.size != 1:
        return None
    return float(arr.reshape(-1)[0])


def _resolve_fps(data: dict[str, np.ndarray], override: float | None) -> tuple[float, str]:
    if override is not None:
        return float(override), "cli"
    for key in ("fps", "mocap_frame_rate"):
        value = _scalar(data, key)
        if value and value > 0:
            return value, key
    return 30.0, "default_30hz"


def _rising_edges(mask: np.ndarray) -> np.ndarray:
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0:
        return np.empty((0,), dtype=int)
    prev = np.concatenate(([False], mask[:-1]))
    return np.flatnonzero(mask & ~prev)


def _contact_bout_lengths(mask: np.ndarray) -> list[int]:
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0:
        return []
    padded = np.concatenate(([False], mask, [False]))
    delta = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(delta == 1)
    ends = np.flatnonzero(delta == -1)
    return [int(e - s) for s, e in zip(starts, ends)]


def _heading_from_posed_joints(posed: np.ndarray) -> tuple[np.ndarray, str] | None:
    """Recover a stable body heading from legacy posed-joint exports.

    The official SOMA30 demo examples use joint 22 = LeftLeg and
    joint 26 = RightLeg. The hip line gives a body-right vector; crossing that
    with world-up gives a forward vector on the XZ plane.
    """
    posed = np.asarray(posed, dtype=float)
    if posed.ndim == 4 and posed.shape[0] == 1:
        posed = posed[0]
    if posed.ndim != 3 or posed.shape[-1] < 3:
        return None
    if posed.shape[1] == 30:
        left = posed[:, 22, :3]
        right = posed[:, 26, :3]
        body_right = right - left
        up = np.zeros_like(body_right)
        up[:, 1] = 1.0
        forward = np.cross(body_right, up)
        horizontal = forward[:, [0, 2]]
        norm = np.linalg.norm(horizontal, axis=1)
        if float(np.median(norm)) > 1e-6:
            angle = np.unwrap(np.arctan2(horizontal[:, 0], horizontal[:, 1]))
            return angle, "soma30_hip_axis"
    return None


def _dominant_frequency(signal: np.ndarray, fps: float) -> float | None:
    x = np.asarray(signal, dtype=float)
    if x.size < 8:
        return None
    x = x - np.mean(x)
    if float(np.std(x)) < 1e-8:
        return None
    spec = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(x.size, d=1.0 / fps)
    valid = freqs >= 0.25
    if not np.any(valid):
        return None
    idxs = np.flatnonzero(valid)
    idx = idxs[int(np.argmax(spec[valid]))]
    return float(freqs[idx])


def analyze_motion(
    data: dict[str, np.ndarray],
    *,
    fps_override: float | None = None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    if "smooth_root_pos" in data:
        root_source = "smooth_root_pos"
        root = np.asarray(data["smooth_root_pos"], dtype=float)
    elif "root_positions" in data:
        root_source = "root_positions"
        root = np.asarray(data["root_positions"], dtype=float)
    elif "posed_joints" in data:
        # Official Kimodo demo examples committed before the newer NPZ schema
        # contain only posed_joints/global_rot_mats/foot_contacts. SOMA30,
        # SOMA77, G1 and SMPL-X all place the skeleton root at joint index 0,
        # so recover the root trajectory from posed_joints[:, 0, :].
        posed = np.asarray(data["posed_joints"], dtype=float)
        if posed.ndim == 4 and posed.shape[0] == 1:
            posed = posed[0]
        if posed.ndim != 3 or posed.shape[2] < 3:
            raise ValueError(f"posed_joints must have shape [T,J,3], got {posed.shape}")
        root_source = "posed_joints[:,0,:]"
        root = posed[:, 0, :]
    else:
        raise ValueError(
            "NPZ must contain smooth_root_pos, root_positions, or posed_joints"
        )

    if root.ndim == 3 and root.shape[0] == 1:
        root = root[0]
    if root.ndim != 2 or root.shape[1] < 3:
        raise ValueError(f"{root_source} must resolve to shape [T,3], got {root.shape}")

    t = int(root.shape[0])
    if t < 2:
        raise ValueError("Motion must contain at least two frames")

    fps, fps_source = _resolve_fps(data, fps_override)
    if fps <= 0:
        raise ValueError("FPS must be positive")
    dt = 1.0 / fps
    duration = (t - 1) * dt

    horizontal = root[:, [0, 2]]
    velocity_xz = np.gradient(horizontal, dt, axis=0)
    speed = np.linalg.norm(velocity_xz, axis=1)
    accel = np.gradient(speed, dt)

    heading = None
    heading_source = None
    if "global_root_heading" in data:
        heading_vec = np.asarray(data["global_root_heading"], dtype=float)
        if heading_vec.ndim == 3 and heading_vec.shape[0] == 1:
            heading_vec = heading_vec[0]
        if heading_vec.shape == (t, 2):
            heading = np.unwrap(np.arctan2(heading_vec[:, 1], heading_vec[:, 0]))
            heading_source = "global_root_heading"

    if heading is None and "posed_joints" in data:
        recovered = _heading_from_posed_joints(np.asarray(data["posed_joints"]))
        if recovered is not None:
            heading, heading_source = recovered

    if heading is None and "global_rot_mats" in data:
        rots = np.asarray(data["global_rot_mats"], dtype=float)
        if rots.ndim == 5 and rots.shape[0] == 1:
            rots = rots[0]
        if rots.ndim == 4 and rots.shape[0] == t and rots.shape[-2:] == (3, 3):
            forward = rots[:, 0, :, 2]
            horizontal_forward = forward[:, [0, 2]]
            if float(np.median(np.linalg.norm(horizontal_forward, axis=1))) > 1e-6:
                heading = np.unwrap(np.arctan2(horizontal_forward[:, 0], horizontal_forward[:, 1]))
                heading_source = "root_global_rotation"

    if heading is None:
        heading = np.unwrap(np.arctan2(velocity_xz[:, 0], velocity_xz[:, 1]))
        heading_source = "root_velocity_fallback"

    turn_rate = np.gradient(heading, dt)
    vertical = root[:, 1]
    vertical_freq = _dominant_frequency(vertical, fps)

    left_contact = None
    right_contact = None
    contact_summary: dict[str, Any] = {"available": False}
    if "foot_contacts" in data:
        contacts = np.asarray(data["foot_contacts"])
        if contacts.ndim == 3 and contacts.shape[0] == 1:
            contacts = contacts[0]
        if contacts.ndim == 2 and contacts.shape[0] == t and contacts.shape[1] >= 4:
            active = contacts[:, :4] > 0.5
            left_contact = active[:, 0] | active[:, 1]
            right_contact = active[:, 2] | active[:, 3]
            left_onsets = _rising_edges(left_contact)
            right_onsets = _rising_edges(right_contact)
            all_onsets = np.sort(np.concatenate((left_onsets, right_onsets)))

            left_bouts = _contact_bout_lengths(left_contact)
            right_bouts = _contact_bout_lengths(right_contact)

            contact_summary = {
                "available": True,
                "assumed_order": ["left_heel", "left_toe", "right_heel", "right_toe"],
                "left_stance_ratio": float(np.mean(left_contact)),
                "right_stance_ratio": float(np.mean(right_contact)),
                "left_contact_onsets": int(left_onsets.size),
                "right_contact_onsets": int(right_onsets.size),
                "combined_step_rate_hz": float(all_onsets.size / duration) if duration > 0 else None,
                "left_stride_rate_hz": float(left_onsets.size / duration) if duration > 0 else None,
                "right_stride_rate_hz": float(right_onsets.size / duration) if duration > 0 else None,
                "median_left_stance_s": float(np.median(left_bouts) / fps) if left_bouts else None,
                "median_right_stance_s": float(np.median(right_bouts) / fps) if right_bouts else None,
            }

    distance = float(np.sum(np.linalg.norm(np.diff(horizontal, axis=0), axis=1)))
    summary: dict[str, Any] = {
        "frames": t,
        "fps": fps,
        "fps_source": fps_source,
        "duration_s": duration,
        "root_source": root_source,
        "heading_source": heading_source,
        "horizontal_distance_m": distance,
        "mean_speed_mps": float(np.mean(speed)),
        "median_speed_mps": float(np.median(speed)),
        "max_speed_mps": float(np.max(speed)),
        "mean_abs_accel_mps2": float(np.mean(np.abs(accel))),
        "max_abs_accel_mps2": float(np.max(np.abs(accel))),
        "mean_abs_turn_rate_deg_s": float(np.degrees(np.mean(np.abs(turn_rate)))),
        "max_abs_turn_rate_deg_s": float(np.degrees(np.max(np.abs(turn_rate)))),
        "vertical_root_std_m": float(np.std(vertical)),
        "vertical_root_dominant_hz": vertical_freq,
        "foot_contacts": contact_summary,
    }

    series: dict[str, np.ndarray] = {
        "frame": np.arange(t, dtype=int),
        "time_s": np.arange(t, dtype=float) / fps,
        "root_x_m": root[:, 0],
        "root_y_m": root[:, 1],
        "root_z_m": root[:, 2],
        "speed_mps": speed,
        "accel_mps2": accel,
        "heading_rad": heading,
        "turn_rate_rad_s": turn_rate,
    }
    if left_contact is not None and right_contact is not None:
        series["left_contact"] = left_contact.astype(np.int8)
        series["right_contact"] = right_contact.astype(np.int8)

    return summary, series


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as z:
        return {key: np.asarray(z[key]) for key in z.files}


def write_csv(path: Path, series: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(series.keys())
    rows = len(series[fields[0]])
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        for i in range(rows):
            writer.writerow([series[name][i].item() for name in fields])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("motion", type=Path)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    parser.add_argument("--timeseries", type=Path, default=None)
    args = parser.parse_args()

    data = load_npz(args.motion)
    summary, series = analyze_motion(data, fps_override=args.fps)

    rendered = json.dumps(summary, indent=2, ensure_ascii=False)
    print(rendered)

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(rendered + "\n", encoding="utf-8")
    if args.timeseries:
        write_csv(args.timeseries, series)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
