#!/usr/bin/env python3
"""
Copies the car photos (still hosted on the old WordPress site) into
public_html/assets/img/cars as compressed WebP files, so the site does not
depend on that site and the photos load faster. Runs in the GitHub Action
before the build; files that already exist are skipped.
"""
import io, json, os, re, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, '..', 'public_html', 'assets', 'img', 'cars'))


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def main():
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    cat = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
    for car in cat['cars']:
        src = car.get('img') or ''
        dest = os.path.join(OUT, slug(car['name']) + '.webp')
        if not src.startswith('http') or os.path.exists(dest):
            continue
        try:
            data = urllib.request.urlopen(urllib.request.Request(src, headers={'User-Agent': 'KWIKAR-build'}), timeout=30).read()
            im = Image.open(io.BytesIO(data))
            im = im.convert('RGBA') if im.mode in ('P', 'LA') else im
            im.thumbnail((900, 900))
            if im.mode == 'RGBA':
                bg = Image.new('RGB', im.size, (238, 241, 246))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            im.convert('RGB').save(dest, 'WEBP', quality=76, method=6)
            print('saved', dest, os.path.getsize(dest))
        except Exception as err:
            print('skip', src, err)


if __name__ == '__main__':
    main()
