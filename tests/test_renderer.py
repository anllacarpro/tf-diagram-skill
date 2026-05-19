import os
import pytest

pytest.importorskip('matplotlib', reason='matplotlib not installed — skip renderer tests')


def test_k8s_fallback_icon_key_matches_detect_provider():
    """FALLBACK_ICONS must use key 'k8s' to match detect_provider output."""
    from lib.renderer import FALLBACK_ICONS

    assert 'k8s' in FALLBACK_ICONS, (
        "FALLBACK_ICONS has no 'k8s' key — detect_provider returns 'k8s' not 'kubernetes'"
    )
    assert 'kubernetes' not in FALLBACK_ICONS, (
        "'kubernetes' key is dead — remove it to avoid confusion"
    )


def test_load_icon_returns_fallback_for_unknown_k8s_resource():
    """load_icon for an unmapped k8s resource type must return a non-None image."""
    from lib.renderer import load_icon, ICONS_DIR

    icons_downloaded = os.path.exists(os.path.join(ICONS_DIR, '.downloaded'))
    if not icons_downloaded:
        pytest.skip('Icons not downloaded — run scripts/download_icons.py first')

    img = load_icon('kubernetes_unknown_resource_xyz')
    assert img is not None, "Fallback icon not returned for unknown k8s resource"


def test_divider_and_legend_x_positions_match():
    """The divider line and legend panel must share the same X ratio."""
    import re

    src_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'scripts', 'lib', 'renderer.py'
    )
    src = open(src_path, encoding='utf-8').read()

    # Extract divider X: ax.plot([W*X, W*X], ...)
    divider_match = re.search(r'ax\.plot\(\[W\*([\d.]+),', src)
    # Extract legend X: LX = W*X
    legend_match = re.search(r'LX\s*=\s*W\*([\d.]+)', src)

    assert divider_match, "Divider ax.plot line not found"
    assert legend_match, "LX = W*... line not found"

    divider_ratio = float(divider_match.group(1))
    legend_ratio = float(legend_match.group(1))

    assert abs(divider_ratio - legend_ratio) < 0.001, (
        f"Divider at W*{divider_ratio} but legend at W*{legend_ratio} — they must match"
    )
