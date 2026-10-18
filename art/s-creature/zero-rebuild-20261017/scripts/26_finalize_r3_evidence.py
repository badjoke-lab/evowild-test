"""Cross-check final saved-file renders and make a real-pixel macro comparison."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/R3_FINAL_LOCAL_CHECKS.json'
assert not OUT.exists()
save = json.loads((ROOT / 'evidence/R3_SAVE.json').read_text())
audit = json.loads((ROOT / 'evidence/VERIFY_S_ZERO_CANDIDATE_REVISED_R3_RELOAD.json').read_text())
source_hash = hashlib.sha256((ROOT / save['model']).read_bytes()).hexdigest()
assert source_hash == save['sha256'] == audit['file_sha256'][save['model']]
checks = []
for final, baseline in [('revised_r3', 'r2_recovery'), ('revised_r3_close', 'r2_foot_close')]:
    current = json.loads((ROOT / 'evidence' / ('RENDER_' + final + '.json')).read_text())
    old = json.loads((ROOT / 'evidence' / ('RENDER_' + baseline + '.json')).read_text())
    assert current['source_sha256'] == source_hash
    assert set(current['views']) == set(old['views'])
    for view, r in current['views'].items():
        assert r['camera_matrix'] == old['views'][view]['camera_matrix']
        assert r['ortho_scale'] == old['views'][view]['ortho_scale']
        p = ROOT / r['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
        checks.append({'render': r['file'], 'same_camera_as_r2': True, 'saved_r3_source_verified': True})

trial_checks = []
for final, trial, views in [('revised_r3', 'r3_trial_b', ['SIDE', 'FRONT', 'FRONT34']),
                            ('revised_r3_close', 'r3_trial_b_close', ['SIDE', 'FRONT34'])]:
    for view in views:
        a = Image.open(ROOT / 'renders' / final / (view + '.png')).convert('RGB')
        b = Image.open(ROOT / 'renders' / trial / (view + '.png')).convert('RGB')
        assert ImageChops.difference(a, b).getbbox() is None
        trial_checks.append({'final': final, 'view': view, 'rgb_pixels_equal_to_reviewed_trial_b': True})

font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 23)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
canvas = Image.new('RGB', (1800, 1350), '#edf1f5')
sources = {}


def read(path):
    sources[str(path.relative_to(ROOT.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')


def panel(picture, col, row, label):
    x, y = col * 600, row * 650
    ImageDraw.Draw(canvas).text((x + 12, y + 10), label, font=font, fill='#162435')
    im = ImageOps.contain(picture, (584, 600))
    canvas.paste(im, (x + (600 - im.width) // 2, y + 43 + (600 - im.height) // 2))


ref = read(ROOT.parent / 'references/00_s_type_modeling_image_v1.png')
for row, (view, crop) in enumerate([('SIDE', (749, 697, 863, 861)), ('FRONT34', (1169, 406, 1279, 508))]):
    panel(ref.crop(crop), 0, row, 'REFERENCE / ' + view + ' FOOT')
    panel(read(ROOT / 'renders/r2_foot_close' / (view + '.png')), 1, row, 'R2 / ' + view + ' CLOSE')
    panel(read(ROOT / 'renders/revised_r3_close' / (view + '.png')), 2, row, 'R3 / ' + view + ' CLOSE')
ImageDraw.Draw(canvas).text((12, 1312), 'Real 900px Blender renders; matching R2/R3 cameras, lights and materials. Reference pose/projection differs.', font=small, fill='#162435')
target = ROOT / 'comparisons/REVISED_R3_FOOT_CLOSE_COMPARISON.png'
assert not target.exists()
canvas.save(target)
OUT.write_text(json.dumps({'r3_sha256': source_hash, 'render_checks': checks,
    'reviewed_trial_to_saved_r3_pixels': trial_checks,
    'protected_files_verified': len(audit['protected_file_sha256']),
    'changed_mesh_count': len(audit['changed_meshes']), 'unchanged_mesh_count': len(audit['unchanged_meshes']),
    'macro_comparison': str(target.relative_to(ROOT)), 'macro_source_sha256': sources,
    'comparison_method': 'Real pixels, cropping, proportional resizing, labels; no shape retouching.',
    'overall': 'REVISE', 'production_keep': False}, indent=2) + '\n')
print('FINAL_R3_LOCAL_CHECKS_PASS', len(checks), 'final renders;', len(trial_checks), 'pixel-equal reviewed views')
