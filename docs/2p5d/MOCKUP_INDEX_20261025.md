# EvoWild Run — user-provided 2.5D mock image register

**Status: reference catalog locked / PNG binary transfer outstanding.** Images were provided in the 2026-10-24 conversation. This repository branch has the **verified SHA-256 inventory and deterministic importer**, but do **not** claim the PNG bytes are in GitHub until the verification script passes. The user can attach `evowild-2p5d-codex-mockups-originals.zip` to Codex and unpack it at the repository root; that ZIP has the original user-shared images, not invented new mocks.

## Exact filenames and purpose

| ID | GitHub checkout target | SHA-256 | Screen |
|---|---|---|---|
| 01 | `docs/2p5d/mockups/01-race-agent-orb-race.png` | `87af2121e2ba7b503c80efc7eabbafa573cf9fe59fe23bb7f260a5f7636ff6e7` | レース中の自律Race Agentオーブ・指令・結果 |
| 02 | `docs/2p5d/mockups/02-race-agent-settings.png` | `c8b78fddc0b595b600a85742bd3249e6359e7c27ccdf3bb880c017fb4d3cea20` | レース開始前のAgent 7項目設定とオーブ説明 |
| 03 | `docs/2p5d/mockups/03-home.png` | `388a6f6cab77f02b9fa56de50227420cf099710637d3300cdb12b801b92240a4` | ゲームのホームメニュー |
| 04 | `docs/2p5d/mockups/04-course-selection.png` | `cdf8cec6ac4204a6f87bcd7996b527feb1a65d9c2443c0bfeb98d57fd0dbfacd` | 競馬場型のコース選択・周回コース情報 |
| 05 | `docs/2p5d/mockups/05-race-entry.png` | `20731fded8b9d13ec489f39a96a7a45bd5e87f633ca64f80c84a3dcd457ffe15` | 出走個体・Agent・レース条件確認 |
| 06 | `docs/2p5d/mockups/06-display-settings.png` | `e1e33ff09e2fd3215da9802959d343ca623cf6843b1735b1c5176b78b58ac7d0` | レース中のカメラ・HUD・Agent表示設定 |
| 07 | `docs/2p5d/mockups/07-race-results.png` | `6e7ed8c3667378426cee4dc97661998ca6b8f92b28e3cd8841b06ab06f938821` | 順位・スタミナ推移・Agent判断の事後確認 |
| 08 | `docs/2p5d/mockups/08-pedigree-history.png` | `3b7a6289356f4cfd444f579eb7cc0e6b491b09804c27d6128a06a7bc03d3edf6` | 血統・戦績・相性履歴の情報構造 |
| 09 | `docs/2p5d/mockups/09-creature-stable.png` | `8bd2f176eb90b9aaf2c3aaa5e6e290031d13619c3eb5291184f9f1611db22264` | 個体一覧と厩舎詳細 |
| 10 | `docs/2p5d/mockups/10-training.png` | `f03f6e21e44c7a60423a9dbae0e363673547e6bca269943cb993c00dedcaafd7` | 育成・調整の画面構成（仕様数値は未確定） |
| 12 | `docs/2p5d/mockups/12-breeding.png` | `6ca1139b85f03282160b4cd81c608c12838bda7da47113a4a6579674b22951e9` | 繁殖と子世代予測の画面構成（遺伝法則は未確定） |

Each original PNG is 1672×941; detailed dimensions, length and checksums are in `docs/2p5d/mockups/manifest.json`. There is no 11: this is **not** a missing-asset error.

## Acceptance classification (do not silently elevate visual details into rules)

1. **Authorised visual direction:** stadium/horse-racing-style oval track (but no countries or real-world venues); behind-and-above chase camera; actual race-grade foot contact and speed feel; 18-entrant foundation; Race Agent is a **non-humanoid mechanical-like glowing orb above/behind each Creature**, different command glows / brief popups / result cues; dark navy HUD; home/course/entry/Agent/settings/results/lineage/stable/training/breeding are design targets.
2. **Not accepted as game rules:** example names, level numbers, roster size ownership cap, gender display, rarity, money, coin balance, wallet payment, race schedule, 1/3 cup races, exact course title or 1800m, exact 8/12/18 field sizes, training gains, stat grades or radar axes, breeding probabilities, lifecycle length, ranks, status colors, Agent-in-game owner/market, live AI features, names of invented locations. These are artwork labels only.
3. **Creature appearance:** reference sheet `docs/references/evowild-creature-reference-sheet-20260921.jpg` and per-morph `public/concept/{S,P,E,A}.webp` are canonical; the **mock illustrations are not source assets or licenses to redesign**.
4. **Race Agent configuration:** exactly the seven categories and common Agent File / Validator direction from `docs/race-agent-spec-v0.1.md`. Race is *spectated* after start, no player-issued live commands; all entrants use the same schema; no external AI live-control advantage.
5. **Course:** oval, rail, grandstand, start/finish, corners and physically coherent course geometry first. The submitted course screen is a visual direction, not authorization for arbitrary wilderness/forest/desert/snow maps or real-country categories.
6. **Unapproved mechanics:** if the mock conflicts with project spec or introduces a system not written in spec, **do not implement it**. Mark as TBD in PR instead of inventing rules.

### Required visual comparison

For every changed screen attach a **real screenshot** (desktop and Android viewport where applicable), side-by-side with the appropriate verified mock, and write a visual difference list. Reject composite images that portray unimplemented 3D locomotion. No new mock generation unless the user explicitly asks.

### Restoring original images

The images are packaged for Codex as `evowild-2p5d-codex-mockups-originals.zip` in this conversation. Put the contents in this repo, preserving bytes, and run:

```bash
python3 scripts/verify_2p5d_mockups.py
```

If missing, **stop UI visual acceptance/reinterpretation** and report `REFERENCE_IMAGE_MISSING`; do not silently reconstruct from text or substitute generated images. Functional tests and non-visual fixes may proceed.
