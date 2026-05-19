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
