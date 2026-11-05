# usage: uv run --with pillow sheet.py VIDEO OUT.jpg t1 t2 ...  -> grid of 320px frames labeled with index and time
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw
vid, out, ts = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3:]]
d = tempfile.mkdtemp(); ims = []
for k, t in enumerate(ts):
    f = f'{d}/{k}.jpg'
    subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-ss',f'{t:.2f}','-i',vid,'-frames:v','1','-vf','scale=320:-2',f], check=False)
    im = Image.open(f).convert('RGB') if os.path.exists(f) else Image.new('RGB', (320, 180))
    ImageDraw.Draw(im).rectangle([0, 0, 120, 16], fill=(0, 0, 0))
    ImageDraw.Draw(im).text((3, 2), f'#{k} {int(t//60)}:{t%60:04.1f}', fill=(255, 255, 0))
    ims.append(im)
cols = 6; w, h = 320, max(i.height for i in ims) if ims else 180
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols*w, rows*h), (40, 40, 40))
for k, im in enumerate(ims): sheet.paste(im, ((k % cols)*w, (k//cols)*h))
sheet.save(out, quality=80)
