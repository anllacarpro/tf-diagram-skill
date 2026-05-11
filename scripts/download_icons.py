#!/usr/bin/env python3
"""
download_icons.py — Downloads official cloud icons from the diagrams package wheel.
Run once: python3 scripts/download_icons.py
Icons saved to: scripts/icons/{aws,gcp,azure,k8s}/...
"""
import urllib.request, zipfile, io, os, sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(SKILL_DIR, 'icons')

WHEEL_URL = (
    'https://files.pythonhosted.org/packages/76/60/'
    '83bb3b6c9ed994e2e6829c01261b64fdcbc0b7e239434be5c417a5e05bb2/'
    'diagrams-0.25.1-py3-none-any.whl'
)

PROVIDERS = ['aws', 'gcp', 'azure', 'k8s']

def main():
    # Check if already downloaded
    marker = os.path.join(ICONS_DIR, '.downloaded')
    if os.path.exists(marker):
        existing = sum(len(f) for _, _, f in os.walk(ICONS_DIR))
        print(f'✅  Icons already downloaded ({existing} files). Delete {marker} to re-download.')
        return

    print('📥  Downloading diagrams wheel (~34 MB)...')
    try:
        req = urllib.request.Request(WHEEL_URL, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print(f'❌  Download failed: {e}')
        print('    Try: pip install diagrams --break-system-packages')
        print('    Then find the icon path with:')
        print('    python3 -c "import diagrams,os; print(os.path.dirname(diagrams.__file__))"')
        sys.exit(1)

    print(f'   Downloaded {len(data)//1024} KB')
    print('📦  Extracting icons...')

    zf = zipfile.ZipFile(io.BytesIO(data))
    pngs = [n for n in zf.namelist()
            if n.endswith('.png') and any(f'/'+p+'/' in n for p in PROVIDERS)]

    os.makedirs(ICONS_DIR, exist_ok=True)
    count = 0
    for name in pngs:
        # resources/aws/compute/eks.png → icons/aws/compute/eks.png
        rel = name.replace('resources/', '', 1)
        dest = os.path.join(ICONS_DIR, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(zf.read(name))
        count += 1

    # Write marker
    open(marker, 'w').write(f'downloaded {count} icons\n')
    print(f'✅  {count} icons saved to {ICONS_DIR}')
    print()
    print('Providers available:')
    for p in PROVIDERS:
        pdir = os.path.join(ICONS_DIR, p)
        if os.path.exists(pdir):
            n = sum(len(fs) for _, _, fs in os.walk(pdir))
            print(f'   {p:12s} {n} icons')

if __name__ == '__main__':
    main()
