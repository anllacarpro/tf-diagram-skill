#!/usr/bin/env python3
"""
tf_to_diagram.py — Main entrypoint for the terraform-diagram skill.

Usage:
    python3 tf_to_diagram.py <terraform_dir> [options]

Options:
    --output, -o  PATH   Output .drawio file (default: <project_name>.drawio)
    --png         PATH   Also render a PNG preview image
    --verbose, -v        Print full resource table
    --no-png             Skip PNG rendering (faster, drawio only)

Examples:
    python3 tf_to_diagram.py ~/projects/infra --output arch.drawio --png arch.png
    python3 tf_to_diagram.py . --verbose
"""

import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.parser  import parse_project
from lib.drawio  import build_drawio
from lib.renderer import render_diagram


def main():
    ap = argparse.ArgumentParser(description='Terraform → Architecture Diagram')
    ap.add_argument('terraform_dir', help='Path to Terraform project root')
    ap.add_argument('--output', '-o', default=None, help='Output .drawio path')
    ap.add_argument('--png', default=None, help='Output PNG path')
    ap.add_argument('--verbose', '-v', action='store_true', help='Print resource table')
    ap.add_argument('--no-png', action='store_true', help='Skip PNG rendering')
    args = ap.parse_args()

    tf_dir = os.path.abspath(args.terraform_dir)
    if not os.path.isdir(tf_dir):
        print(f'ERROR: "{tf_dir}" is not a directory.'); sys.exit(1)

    project_name = os.path.basename(tf_dir)

    # Default output paths
    drawio_out = args.output or f'{project_name}.drawio'
    png_out    = args.png
    if not args.no_png and not png_out:
        png_out = drawio_out.replace('.drawio', '') + '.png'

    print(f'🔍  Scanning: {project_name}  ({tf_dir})')
    tf_data = parse_project(tf_dir)

    # Summary
    r     = len(tf_data['resources'])
    ds    = len(tf_data['data'])
    mod   = len(tf_data['modules'])
    dep   = len(tf_data['dependencies'])
    provs = sorted(tf_data['providers'].keys())
    regs  = sorted(tf_data['regions'])
    accs  = sorted(tf_data['accounts'])
    miss  = sum(1 for x in tf_data['resources'].values() if not x.get('has_tags'))

    print(f'\n📊  Summary:')
    print(f'   Resources    : {r}')
    print(f'   Data sources : {ds}')
    print(f'   Modules      : {mod}')
    print(f'   Dependencies : {dep}')
    print(f'   Providers    : {", ".join(provs) or "none detected"}')
    print(f'   Regions      : {", ".join(regs) or "n/a"}')
    print(f'   Accounts/Env : {", ".join(accs) or "n/a"}')
    if miss:
        print(f'   ⚠️  Missing tags: {miss} resources')
    else:
        print(f'   Tags         : ✅ all resources tagged')

    if args.verbose:
        print(f'\n📋  Resources:')
        for key, rd in sorted(tf_data['resources'].items()):
            tag_w = ' ⚠️  NO TAGS' if not rd.get('has_tags') else ''
            net   = '  [' + ' | '.join(rd.get('net_info', [])) + ']' if rd.get('net_info') else ''
            print(f'   [{rd["provider"]:12}] [{rd["tier"]:12}] {key:55} {rd["region"]:22}{tag_w}{net}')

    if r == 0 and ds == 0:
        print('\n⚠️  No resources found. Check that .tf files exist in the directory.')
        sys.exit(1)

    # Generate draw.io
    scopes = set((rd.get('account','default'), rd.get('region','?'))
                 for rd in tf_data['resources'].values())
    pages = len(scopes) + 1  # +1 for Legend

    print(f'\n🎨  Building draw.io ({pages} pages: {", ".join(f"{a}/{r}" for a,r in sorted(scopes))} + Legend)...')
    xml = build_drawio(tf_data, project_name)

    with open(drawio_out, 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'   ✅  {drawio_out}')

    # Generate PNG
    if png_out and not args.no_png:
        print(f'\n🖼   Rendering PNG...')
        try:
            import matplotlib
            render_diagram(tf_data, project_name, png_out)
        except ImportError:
            print('   ⚠️  matplotlib not installed. Skipping PNG.')
            print('       Run: pip install matplotlib --break-system-packages')

    print(f'\n✅  Done!')
    print(f'   → Open .drawio at: https://app.diagrams.net  (drag & drop)')
    print(f'   → VS Code: install "Draw.io Integration" extension (hediet.vscode-drawio)')
    if miss:
        print(f'\n   ⚠️  {miss} resources without tags — shown with red border in diagram')
    print()


if __name__ == '__main__':
    main()
