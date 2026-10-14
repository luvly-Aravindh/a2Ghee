"""Turn product.html into a Shopify page template.

Run from the project folder:   python shopify/build.py

Writes:
  shopify/templates/page.a2-ghee.liquid   the page, with local media pointed at the theme's assets
  shopify/assets/                         every local media file the page uses, ready to upload

Served from eliqonaturals.com, the page's Add to Cart opens the cart drawer on the store's real cart.
"""
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'shopify'
SRC = ROOT / 'product.html'

html = SRC.read_text(encoding='utf-8')
if '{{' in html or '{%' in html:
    raise SystemExit('product.html contains {{ or {% which Shopify would read as Liquid; escape it first.')

used = {}


def to_asset(m):
    rel = m.group(2)
    name = rel.split('/')[-1]  # theme assets are one flat folder
    if name in used and used[name] != rel:
        raise SystemExit(f'Two files share the name {name}: {used[name]} and {rel}')
    used[name] = rel
    return m.group(1) + "{{ '" + name + "' | asset_url }}"


html = re.sub(r'''((?:src|href|data-src|poster)=["'])(?:\./)?(media/[^"'?#]+)''', to_asset, html)
left = re.findall(r'''["'](?:\./)?media/[^"']+''', html)
if left:
    raise SystemExit('Local media paths not converted: ' + ', '.join(sorted(set(left))))

# The reel videos play as .webm where the browser supports it, so ship those too.
for name, rel in list(used.items()):
    if name.endswith('.mp4'):
        webm = rel[:-4] + '.webm'
        if (ROOT / webm).exists():
            used[name[:-4] + '.webm'] = webm

tpl = OUT / 'templates'
assets = OUT / 'assets'
for d in (tpl, assets):
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)

(tpl / 'page.a2-ghee.liquid').write_text('{% layout none %}\n' + html, encoding='utf-8', newline='')
total = 0
for name, rel in sorted(used.items()):
    src = ROOT / rel
    if not src.exists():
        raise SystemExit(f'Missing file: {rel}')
    shutil.copy2(src, assets / name)
    total += src.stat().st_size

print(f'templates/page.a2-ghee.liquid written; {len(used)} asset files ({total / 1e6:.1f} MB) in shopify/assets/')
