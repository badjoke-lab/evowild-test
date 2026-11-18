"""Bake the stadium's transparent run atlases from existing 2D Git artwork.

Run from the repository root after fetching the source branches. Pillow, numpy
and scipy are offline authoring dependencies only. Rows are front, front-right,
right, rear-right and rear. Opposite obliques use bilateral reflection.
"""
import base64
import io
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

CELL = (208, 144)
GROUND = 136
PHASES = 12
OUT = Path("public/concept/stadium")
ROAD = "f0a14892"
S_DESIGN = "34e92e5f56e12f611b59c62381f7bc1f1ff015bc"


def git_bytes(ref):
    return subprocess.check_output(["git", "show", ref])


def normalized(image, scale, center, foot):
    image = image.resize(tuple(max(1, round(v * scale)) for v in image.size), Image.Resampling.LANCZOS)
    cell = Image.new("RGBA", CELL)
    cell.alpha_composite(image, (round(CELL[0] / 2 - center * scale), round(GROUND - foot * scale)))
    return cell


def side_keys(morph):
    if morph == "p":
        # Twelve individually drawn, phase-ordered P keys. The canonical
        # correction carries its own sole baseline and airborne clearance.
        image = Image.open(io.BytesIO(git_bytes("6c0c7986:public/concept/p-run-sheet.webp"))).convert("RGBA")
        for i in range(12):
            x, y = (i % 4)*416, (i // 4)*320
            yield normalized(image.crop((x,y,x+416,y+320)), .48, 208, 296)
        return
    image = Image.open(f"public/concept/{morph}-run-sheet.webp").convert("RGBA")
    pixels = np.asarray(image)
    labels, _ = ndimage.label(pixels[:, :, 3] > 12, np.ones((3, 3)))
    six = np.argsort(np.bincount(labels.ravel())[1:])[-6:] + 1
    parts = ndimage.find_objects(labels)
    def center(label):
        y, x = parts[label - 1]
        return (x.start+x.stop)/2, (y.start+y.stop)/2
    cols = 2 if morph == "a" else 3
    by_y = sorted(six, key=lambda label: center(label)[1])
    ordered = [label for start in range(0, 6, cols)
               for label in sorted(by_y[start:start+cols], key=lambda label: center(label)[0])]
    keys = []
    for label in ordered:
        region = parts[label-1]
        crop = pixels[region].copy()
        crop[labels[region] != label] = 0
        keys.append(Image.fromarray(crop))
    scale = min(193 / max(k.width for k in keys), 109 / max(k.height for k in keys))
    # The v3 alignment pass set contact/push/land to y=220 and flight to 199.
    # Apply those key heights to intact source outlines. Its fixed-size A cells
    # are only 170px tall and dropped the lower legs when translated to y=220.
    for frame, lift in zip(keys, [0, 0, 9, 21, 15, 0]):
        yield normalized(frame, scale, frame.width / 2, frame.height + lift)


def polygon(image, points):
    mask = Image.new("L", image.size)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    result = image.copy()
    result.putalpha(Image.fromarray(np.minimum(np.asarray(image.getchannel("A")), np.asarray(mask))))
    return result


def flex(layer, root, foot, phase, stride, lift):
    """Inverse-map scan lines about the hip/shoulder and bent knee."""
    box = layer.getbbox()
    if not box:
        return layer
    # Keep the joint embedded in the body while the paw sweeps and folds.
    y = np.arange(layer.height)
    weight = np.clip((y-root)/(foot-root), 0, 1)
    swing = math.cos(phase)
    recovery = max(0, -math.sin(phase))
    bend = np.sin(np.pi * weight) * recovery
    dx = stride * (weight * swing - .70 * bend)
    dy = -lift * recovery * weight**1.4
    sample = np.interp(y, y + dy, y)
    offset = np.interp(sample, y, dx)
    mesh = []
    for top in range(0, layer.height, 4):
        bottom = min(top + 4, layer.height)
        a, b = top, min(bottom, layer.height-1)
        l, r = -offset[a], -offset[b]
        mesh.append(((0, top, layer.width, bottom),
                     (l, sample[a], r, sample[b], layer.width+r, sample[b], layer.width+l, sample[a])))
    return layer.transform(layer.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)


def s_layers(view):
    # Local coordinates on the original, user-supplied S turnaround.
    image = Image.open(io.BytesIO(git_bytes(S_DESIGN))).convert("RGBA").crop((760,70,1430,515))
    rgb = np.asarray(image)[:, :, :3].astype(float)
    # Only remove background connected to the edges, retaining pale body plates.
    light = (rgb.min(2)>189) & (rgb.max(2)-rgb.min(2)<25)
    labels, _ = ndimage.label(light)
    outside = np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
    alpha = ~np.isin(labels, outside[outside != 0])
    image.putalpha(Image.fromarray(alpha.astype('uint8')*255))
    if view in ("front","rear"):
        rear = view == "rear"
        cx = 284 if rear else 101
        # Model-space left limb, in source image. The other is extracted
        # independently so highlights and markings survive the pose change.
        left = [(cx-47,208),(cx-13,212),(cx-12,270),(cx-21,320),(cx-18,402),
                (cx-6,432),(cx-42,432),(cx-38,393),(cx-45,321),(cx-52,274)]
        right = [(2*cx-x,y) for x,y in left]
        legs = [polygon(image,p) for p in [left,right]]
        torso = polygon(image,[(cx-53,208),(cx-28,166),(cx-20,140),(cx-29,89),
                              (cx-22,36),(cx+23,36),(cx+29,90),(cx+20,146),
                              (cx+29,165),(cx+51,209),(cx+50,249),(cx+30,273),
                              (cx+19,261),(cx+6,277),(cx+1,315 if rear else 284),
                              (cx-7,274),(cx-19,259),(cx-31,274),(cx-48,249)])
        return torso, legs, cx
    # Trace the four limbs to separate them where they cross the flank.
    leg_polys = [
        [(429,204),(455,214),(472,241),(464,305),(439,392),(429,431),(394,432),(420,395),(439,313),(444,264)],
        [(535,201),(571,196),(575,234),(569,270),(592,304),(575,349),(566,397),(552,419),(528,419),(548,385),(568,312),(536,268)],
        [(472,205),(503,195),(521,231),(524,289),(533,286),(515,390),(514,430),(482,433),(503,387),(507,307),(494,268)],
        [(567,185),(598,179),(611,201),(613,265),(637,302),(640,360),(649,398),(647,420),(619,420),(631,385),(623,314),(590,275),(580,245)]]
    legs = [polygon(image,p) for p in leg_polys]
    body = polygon(image,[(382,176),(384,131),(405,82),(458,41),(538,15),(526,32),
                           (450,116),(451,147),(480,164),(526,141),(519,165),(571,169),
                           (603,171),(635,196),(654,234),(669,290),(669,331),(645,268),
                           (618,228),(600,216),(578,231),(554,226),(537,241),(520,243),
                           (505,263),(484,253),(468,246),(450,251),(428,223),(431,188),(412,153)])
    if view == 'rearQ':
        # The original has no rear oblique. Lay the dorsal head and rump from
        # the back plate over the oblique neck/flank, hiding the facial planes.
        body = polygon(body,[(410,147),(452,132),(500,141),(670,140),(670,334),
                             (579,260),(508,271),(433,260)])
        back, _, _ = s_layers('rear')
        head = back.crop((255,35,315,175)).resize((68,139),Image.Resampling.LANCZOS)
        rump = back.crop((233,178,336,313)).resize((71,103),Image.Resampling.LANCZOS)
        composite = Image.new('RGBA',image.size)
        composite.alpha_composite(head,(399,28))
        composite.alpha_composite(body)
        composite.alpha_composite(rump,(548,172))
        body = composite
    return body,legs,526


def sprint_row(view):
    body, legs, center = s_layers(view)
    diagonal = len(legs) == 4
    if not diagonal:
        # The axial drawing occludes the far pair. Offset two copies behind
        # the shoulders, shortened in projection and independently articulated.
        far = []
        for i,leg in enumerate(legs):
            copy = leg.resize((leg.width,round(leg.height*.92)),Image.Resampling.LANCZOS)
            plate = Image.new('RGBA',leg.size)
            plate.alpha_composite(copy,(-11 if i==0 else 11,15))
            far.append(plate)
        legs = far + legs
    phases = [.44,.61,0,.15] if diagonal else [.48,.62,0,.14]
    if view=='rear': phases = [0,.14,.48,.62]
    for i in range(PHASES):
        t = i/PHASES
        frame = Image.new('RGBA',body.size)
        posed = [flex(leg,212,430,2*np.pi*(t+p),-64 if diagonal else (9 if j%2 else -9),
                      80 if diagonal else 86) for j,(leg,p) in enumerate(zip(legs,phases))]
        for leg in posed[:2]: frame.alpha_composite(leg)
        frame.alpha_composite(body,(0,round(4*math.sin(2*np.pi*t))))
        for leg in posed[2:]: frame.alpha_composite(leg)
        result = normalized(frame,.273,center,434 + 18 * max(0, -math.cos(2*np.pi*t))**3)
        yield ImageOps.mirror(result) if diagonal else result


def recovered_row(image, row, morph):
    # The historic 36x48 cells contain a vertical ruler, a horizontal grey
    # band and progressively offset subjects. Align to the *subject* centers.
    plates = []
    native = np.array(image.crop((0,row*48,216,(row+1)*48)))
    for x in range(36,216,36):
        # Reconnect the transparent atlas gutters through the moving outlines.
        lo,hi = x-3,x+2
        for k in range(lo+1,hi):
            frac = (k-lo)/(hi-lo)
            native[:,k] = native[:,lo]*(1-frac) + native[:,hi]*frac
    # Outside silhouettes traced in the recovered 44x48 crop. A has a
    # descending tail, E has a narrower waist, P carries a deeper chest.
    head_on = [(10,46),(10,21),(14,18),(14,2),(30,2),(30,18),(33,22),(33,46)]
    if row == 0:
        contour = [(7,28),(8,21),(15,12),(25,2),(33,2),(26,12),(21,19),
                   (27,18),(34,19),(36,23),(40,32),(40,46),(33,46),
                   (30,34),(26,33),(22,40),(21,46),(9,46),(6,44),
                   (10,38),(14,32),(14,28)]
        if morph == 'a':
            contour = [(6,34),(9,23),(18,7),(29,5),(23,16),(20,23),
                       (29,21),(34,24),(37,32),(40,34),(40,46),(34,46),
                       (29,37),(25,36),(20,41),(17,46),(7,46),(10,38),(13,33)]
    elif row == 2:
        contour = [(4,41),(7,30),(10,24),(17,21),(23,20),(16,10),
                   (14,3),(26,7),(31,13),(37,19),(40,24),(40,27),
                   (34,27),(34,33),(38,39),(36,46),(22,46),(19,39),
                   (16,45),(5,46)]
    else:
        contour = head_on
    # Late keys cross the right edge of the stored atlas. Reuse intact keys
    # through gather/reach; the independently posed legs span all 12 phases.
    for k in (0,1,1,0,1,0):
        centers = ([23,61,97],[21,60,99],[26,63,99],[19,56,91])[row]
        cx = centers[k]
        region = Image.fromarray(native).crop((cx-22,0,cx+22,48))
        art = polygon(region,contour)
        pixels = np.array(art)
        yy, xx = np.indices(pixels.shape[:2])
        # Ruler shadows outside the head/chest and along the tail; the dark
        # blue A torso occupies the middle of the crop and must retain ink.
        rgb = pixels[:,:,:3].astype(int)
        grey = (rgb.max(2)-rgb.min(2)<17) & (rgb.mean(2)<119)
        outer = (xx<14) | (xx>34)
        pixels[grey & outer & (yy>18) & (yy<35),3]=0
        # Suppress isolated guide specks without losing separated crest tips.
        labels,_=ndimage.label(pixels[:,:,3]>22,np.ones((3,3)))
        areas=np.bincount(labels.ravel())
        pixels[(labels==0) | (areas[labels]<4),3]=0
        art=Image.fromarray(pixels)
        plate = Image.new('RGBA',(60,52))
        plate.alpha_composite(art,(8,0))
        plates.append(plate)
    for i in range(PHASES):
        original=plates[i//2]
        # Flex opposing limbs below the belly. Each follows its own stance and
        # recovery arc; the torso keeps the recovered source key silhouette.
        root = 29 if row in (1,3) else 28
        cut = 30
        left=polygon(original,[(0,root-2),(cut,root-2),(cut,52),(0,52)])
        right=polygon(original,[(cut+1,root-2),(59,root-2),(59,52),(cut+1,52)])
        t=2*math.pi*i/PHASES
        frame=Image.new('RGBA',original.size)
        stride = {0:-7, 1:2.3, 2:7, 3:2.3}[row]
        for half,offset in ((left,0),(right,.48)):
            frame.alpha_composite(flex(half,root,46,t+2*math.pi*offset,
                                       stride,8))
        upper = original.crop((0,0,60,root+2))
        # Close the shoulder overlap as weight passes over the planted leg.
        frame.alpha_composite(upper,(0,round(math.sin(t) * 1.2)))
        body_height={'p':94,'e':103,'a':86}[morph]
        ground=46
        result=normalized(frame,body_height/(ground-4),30,ground+max(0, -math.cos(t))*2.2)
        yield ImageOps.mirror(result) if row==0 else result


def register_row(frames, target_height):
    # One transform for the whole row preserves compression and flight. Use
    # high-alpha pixels so a Lanczos fringe cannot shift the contact plane.
    keys = list(frames)
    bounds = [frame.getchannel("A").point(lambda a: 255 if a>110 else 0).getbbox() for frame in keys]
    scale = target_height / np.median([b[3]-b[1] for b in bounds])
    scale = min(scale, (CELL[0]-4)/max(b[2]-b[0] for b in bounds))
    foot = max(bounds[i][3] for i in (0,1,len(keys)-1))
    return [normalized(frame,scale,CELL[0]/2,foot) for frame in keys]


def bake(morph):
    if morph=='s':
        rows=[sprint_row('front'),sprint_row('frontQ'),side_keys(morph),sprint_row('rearQ'),sprint_row('rear')]
    else:
        svg=git_bytes(f'{ROAD}:public/concept/{morph}-multidirection-run-atlas.svg')
        embedded=base64.b64decode(re.search(rb'base64,([^"]+)',svg)[1])
        source=Image.open(io.BytesIO(embedded)).convert('RGBA')
        rows=[recovered_row(source,1,morph),recovered_row(source,0,morph),side_keys(morph),
              recovered_row(source,2,morph),recovered_row(source,3,morph)]
    atlas=Image.new('RGBA',(CELL[0]*PHASES,CELL[1]*len(rows)))
    for row,frames in enumerate(rows):
        for col,frame in enumerate(register_row(frames, {"s":105,"p":100,"e":102,"a":78}[morph])):
            atlas.alpha_composite(frame,(col*CELL[0],row*CELL[1]))
    atlas.save(OUT/f'{morph}-run.webp',lossless=True,method=4)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True,parents=True)
    for morph in 'spea':
        bake(morph)
