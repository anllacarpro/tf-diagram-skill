import xml.etree.ElementTree as ET
import pytest


def _page0_cell_ids(xml_str):
    """Return the set of mxCell id values from the first diagram page."""
    tree = ET.fromstring(xml_str.split('\n', 1)[1])
    diag = tree.find('diagram')
    if diag is None:
        return set()
    return {c.get('id', '') for c in diag.iter('mxCell') if c.get('id')}


def test_build_drawio_counter_resets_between_calls(minimal_tf_data):
    """Two successive calls must produce identical cell-ID sets for page 0."""
    from lib.drawio import build_drawio

    xml1 = build_drawio(minimal_tf_data, 'run1')
    xml2 = build_drawio(minimal_tf_data, 'run2')

    ids1 = _page0_cell_ids(xml1)
    ids2 = _page0_cell_ids(xml2)

    assert ids1 == ids2, (
        f"Counter not reset between calls.\n"
        f"Run 1 IDs: {sorted(ids1)}\n"
        f"Run 2 IDs: {sorted(ids2)}"
    )
