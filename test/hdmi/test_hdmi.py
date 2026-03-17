import importlib
import sys
from typing import List


MODETEST_SAMPLE = """
Connectors:
id	encoder	status		name		size (mm)	modes	encoders
30	25	connected	HDMI-A-1	160x90		4	25
modes:
index name refresh (Hz) hdisp hss hse htot vdisp vss vse vtot)
#0 3840x2160 60.00 3840 4016 4104 4400 2160 2168 2178 2250  594000 flags: phsync, pvsync; type: preferred, cta, est3, dmt
#1 3840x2160 50.00 3840 4016 4104 5280 2160 2168 2178 2250  587000 flags: phsync, pvsync; type: cta, dmt
#2 2560x1440 59.95 2560 2728 2792 3560 1440 1481 1488 1500  241500 flags: phsync, pvsync; type: dmt
""".strip()

MODETEST_WITH_CRTC_SAMPLE = """
Encoders:
id	crtc	type	possible crtcs	possible clones
25	51	TMDS	0x00000001	0x00000001

Connectors:
id	encoder	status		name		size (mm)	modes	encoders
30	25	connected	HDMI-A-1	160x90		4	25
modes:
index name refresh (Hz) hdisp hss hse htot vdisp vss vse vtot)
#0 1920x1080 60.00 1920 2008 2052 2200 1080 1084 1089 1125  148500 flags: phsync, pvsync; type: driver
#1 1280x720 60.00 1280 1390 1430 1650 720 725 730 750  74250 flags: phsync, pvsync; type: preferred, driver

CRTCs:
id	fb	pos	size
51	55	(0,0)	(1280x720)
""".strip()

def test_build_basic_entries_from_modetest(monkeypatch):
    """Builds flat unique resolutions from modetest data."""
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_run_modetest", lambda: MODETEST_SAMPLE)  # pylint: disable=protected-access

    modes = hdmi._parse_modetest_modes()  # pylint: disable=protected-access
    out = hdmi._build_basic_entries(modes)  # pylint: disable=protected-access

    assert [entry["value"] for entry in out] == ["3840x2160", "2560x1440"]


def test_main_listing_format(monkeypatch, capsys):
    """Lists simplified CLI output: '0 - auto' and flat entries without headers."""
    entries: List[dict] = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "mode", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {"kind": "mode", "title": "3840x2160", "name": "3840x2160", "payload": ""},
        {
            "kind": "edid",
            "title": "3840x2160-60.00 (EDID - 594MHz)",
            "name": "3840x2160-60.00",
            "payload": '"3840x2160-60.00" 594 3840 4016 4104 4400 2160 2168 2178 2250 +hsync +vsync',
        },
        {
            "kind": "cvt",
            "title": "3840x2160-60.00 (VESA CVT - 712.75MHz)",
            "name": "3840x2160-60.00",
            "payload": '"3840x2160-60.00" 712.75 3840 4016 4104 4400 2160 2168 2178 2250 +hsync +vsync',
        },
    ]

    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    # Simulate CLI with no args
    monkeypatch.setattr(sys, "argv", ["hdmi.py"])  # nosec: B104 test adjusts argv
    ret = hdmi.main()
    assert ret == 0
    out = capsys.readouterr().out.strip().splitlines()
    # First line is simplified auto entry
    assert out[0] == "0 - auto"
    # No section headers present
    assert not any(line.startswith("2)") or line.startswith("3)") for line in out)
    # Next lines are a flat sequence of titles from entries
    assert any("1920x1080" in line for line in out)
    assert any(("3840x2160-60.00 (EDID" in line) or ("VESA CVT" in line) for line in out)


def test_apply_by_index_flat_mode(monkeypatch, capsys):
    """Flat mode entries are list-only and do not print a Modeline."""
    entries = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "mode", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {
            "kind": "edid",
            "title": "1920x1080-60.00 (EDID - 148.50MHz)",
            "name": "1920x1080-60.00",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    rc = hdmi._apply_by_index("1")  # pylint: disable=protected-access
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_apply_by_index_detailed(monkeypatch):
    """Detailed EDID mode prints its Modeline payload."""
    entries = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "mode", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {
            "kind": "edid",
            "title": "1920x1080-60.00 (EDID - 148.50MHz)",
            "name": "1920x1080-60.00",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    rc = hdmi._apply_by_index("2")  # pylint: disable=protected-access
    assert rc == 0
    # Payload is printed to stdout by _apply_by_index


def test_get_hdmi_modes_not_installed(monkeypatch):
    """When wb-hdmi is not installed, exposes a single auto entry with a hint."""
    hdmi = importlib.import_module("hdmi")

    # Simulate dpkg-query failure (package not installed)
    def fake_check_output(args, text=False):  # pylint: disable=unused-argument
        raise hdmi.subprocess.CalledProcessError(returncode=1, cmd=args)

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)

    out = hdmi.get_hdmi_modes()
    assert isinstance(out, list) and len(out) == 1
    assert out[0]["value"] == "auto"
    assert "wb-hdmi" in out[0]["title"]


def test_get_hdmi_modes_installed(monkeypatch):
    """When wb-hdmi is installed, returns grouped entries (may include auto)."""
    hdmi = importlib.import_module("hdmi")

    # Simulate package installed
    def fake_check_output(args, text=False):  # pylint: disable=unused-argument
        return "install ok installed\n"

    entries: List[dict] = [
        {"kind": "auto", "value": "auto", "title": "Auto from EDID"},
        {"kind": "mode", "value": "1920x1080", "title": "1920x1080"},
        {
            "kind": "edid",
            "value": "1920x1080-60.00|EDID:148500",
            "title": "1920x1080-60.00 (EDID - 148.50MHz)",
        },
        {
            "kind": "cvt",
            "value": "1920x1080-60.00|CVT:173000",
            "title": "1920x1080-60.00 (VESA CVT - 173.00MHz)",
        },
    ]

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    out = hdmi.get_hdmi_modes()
    values = [e["value"] for e in out]
    # May include auto now
    assert "auto" in values
    # Includes flat modes and detailed entries
    assert "1920x1080" in values
    assert "1920x1080-60.00|EDID:148500" in values
    assert "1920x1080-60.00|CVT:173000" in values


def test_get_hdmi_modes_legacy_package_installed(monkeypatch):
    """wb-hdmi-xorg should also enable HDMI mode discovery for the UI."""
    hdmi = importlib.import_module("hdmi")

    def fake_check_output(args, text=False):  # pylint: disable=unused-argument
        package = args[-1]
        if package == "wb-hdmi":
            raise hdmi.subprocess.CalledProcessError(returncode=1, cmd=args)
        if package == "wb-hdmi-xorg":
            return "install ok installed\n"
        raise AssertionError("unexpected package query")

    entries: List[dict] = [
        {"kind": "auto", "value": "auto", "title": "Auto from EDID"},
    ]

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    out = hdmi.get_hdmi_modes()
    assert out == [{"value": "auto", "title": "Auto from EDID"}]


def test_cvt_modeline_parsing(monkeypatch):
    """Parses cvt output and returns the Modeline payload (without the word 'Modeline')."""
    hdmi = importlib.import_module("hdmi")

    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args and args[0] == "cvt":
            return 'Modeline "3840x2160_60.00" 533.25 3840 4016 4104 4400 2160 2168 2178 2250 +hsync +vsync\n'
        raise AssertionError("unexpected command")

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    payload = hdmi._cvt_modeline("3840x2160", "60.00")  # pylint: disable=protected-access
    assert payload.startswith('"3840x2160_60.00" 533.25')


def test_cvt_modeline_no_cvt(monkeypatch):
    """Returns empty payload when the 'cvt' tool is missing or fails."""
    hdmi = importlib.import_module("hdmi")

    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args and args[0] == "cvt":
            raise FileNotFoundError
        return ""

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    payload = hdmi._cvt_modeline("3840x2160", "60.00")  # pylint: disable=protected-access
    assert payload == ""


def test_apply_by_index_auto(monkeypatch, capsys):
    """Index 0 prints the Auto Modeline payload."""
    hdmi = importlib.import_module("hdmi")
    entries = [
        {
            "kind": "auto",
            "title": "Auto from EDID",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access

    rc = hdmi._apply_by_index("0")  # pylint: disable=protected-access
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith('"1920x1080-60.00" 148.50')


def test_build_grouped_entries_aggregates(monkeypatch):
    """Aggregates Auto, flat modetest resolutions, and detailed EDID/CVT entries."""
    hdmi = importlib.import_module("hdmi")

    # Provide modetest modes: include >=2.5K widths and one below threshold
    modetest_modes = [
        {
            "idx": 0,
            "res": "3840x2160",
            "refresh": "60.00",
            "hdisp": 3840,
            "hss": 4016,
            "hse": 4104,
            "htot": 4400,
            "vdisp": 2160,
            "vss": 2168,
            "vse": 2178,
            "vtot": 2250,
            "pclk_khz": 594000,
            "hs": "+hsync",
            "vs": "+vsync",
        },
        {
            "idx": 1,
            "res": "2560x1440",
            "refresh": "59.95",
            "hdisp": 2560,
            "hss": 2728,
            "hse": 2792,
            "htot": 3560,
            "vdisp": 1440,
            "vss": 1481,
            "vse": 1488,
            "vtot": 1500,
            "pclk_khz": 241500,
            "hs": "+hsync",
            "vs": "+vsync",
        },
        {
            "idx": 2,
            "res": "1920x1080",
            "refresh": "60.00",
            "hdisp": 1920,
            "hss": 2008,
            "hse": 2052,
            "htot": 2200,
            "vdisp": 1080,
            "vss": 1084,
            "vse": 1089,
            "vtot": 1125,
            "pclk_khz": 148500,
            "hs": "+hsync",
            "vs": "+vsync",
        },
    ]

    monkeypatch.setattr(
        hdmi, "_parse_modetest_modes", lambda: modetest_modes
    )  # pylint: disable=protected-access
    # Ensure CVT is unique so it is added
    monkeypatch.setattr(
        hdmi,
        "_cvt_modeline",
        lambda res, r: f'"{res}-{r}" 700.00 10 20 30 40 50 60 70 80 +hsync +vsync',  # pylint: disable=protected-access
    )

    entries = hdmi._build_grouped_entries()  # pylint: disable=protected-access
    assert entries, "Expected non-empty entries"
    # First entry is auto with preferred mode based on first modetest mode
    assert entries[0]["kind"] == "auto"
    assert entries[0]["name"] == "3840x2160-60.00"

    # Next, flat mode entries should include all unique modetest resolutions
    basic = [e for e in entries if e.get("kind") == "mode"]
    basic_values = {e["value"] for e in basic}
    assert {"3840x2160", "2560x1440", "1920x1080"}.issubset(basic_values)

    # Detailed entries include EDID and CVT for >=2560 widths
    det = [e for e in entries if e.get("kind") in {"edid", "cvt"}]
    names = {e["name"] for e in det}
    assert "3840x2160-60.00" in names
    assert "2560x1440-59.95" in names
    kinds_per_name = {}
    for e in det:
        kinds_per_name.setdefault(e["name"], set()).add(e["kind"])
    # Each name should have at least EDID, and CVT added due to unique tail
    assert "edid" in kinds_per_name["3840x2160-60.00"] and "cvt" in kinds_per_name["3840x2160-60.00"]
    assert "edid" in kinds_per_name["2560x1440-59.95"] and "cvt" in kinds_per_name["2560x1440-59.95"]


def test_build_grouped_entries_no_tools(monkeypatch):
    """With no modetest, returns only the Auto entry with empty payload."""
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_parse_modetest_modes", lambda: [])  # pylint: disable=protected-access

    entries = hdmi._build_grouped_entries()  # pylint: disable=protected-access
    assert len(entries) == 1
    assert entries[0]["kind"] == "auto"
    assert entries[0]["payload"] == ""


# test_get_hdmi_modes_installed_only_auto was removed: Auto may be present in UI list


def test_clean_monitor_field():
    hdmi = importlib.import_module("hdmi")
    assert hdmi._clean_monitor_field("  'Panel 123'  ") == "Panel 123"  # pylint: disable=protected-access


def test_find_connected_hdmi_edid(monkeypatch):
    hdmi = importlib.import_module("hdmi")

    monkeypatch.setattr(
        hdmi.glob,
        "glob",
        lambda pattern: [
            "/sys/class/drm/card0-HDMI-A-1/status",
            "/sys/class/drm/card1-HDMI-A-1/status",
        ],
    )

    def fake_open(path, mode="r", encoding=None):  # pylint: disable=unused-argument
        class FakeFile:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return self.value

        if path.endswith("card0-HDMI-A-1/status"):
            return FakeFile("disconnected\n")
        if path.endswith("card1-HDMI-A-1/status"):
            return FakeFile("connected\n")
        raise AssertionError(f"unexpected open path: {path}")

    monkeypatch.setattr(hdmi, "open", fake_open, raising=False)
    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: path.endswith("card1-HDMI-A-1/edid"))

    find_connected_hdmi_edid = getattr(hdmi, "_find_connected_hdmi_edid")

    assert find_connected_hdmi_edid() == "/sys/class/drm/card1-HDMI-A-1/edid"


def test_read_monitor_name_uses_connected_hdmi(monkeypatch):
    hdmi = importlib.import_module("hdmi")

    monkeypatch.setattr(
        hdmi,
        "_find_connected_hdmi_edid",
        lambda: "/sys/class/drm/card1-HDMI-A-1/edid",
    )  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: True)
    monkeypatch.setattr(hdmi.subprocess, "check_output", lambda *a, **k: "Display Product Name: 'Panel'")

    assert hdmi._read_monitor_name() == "Panel"  # pylint: disable=protected-access


def test_read_monitor_name_prefers_display_product_name(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    edid_output = """
Display Product Name: 'Preferred Name'
Monitor name: 'Fallback'
Manufacturer: 'ACM'
Model: '1234'
""".strip()

    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: True)
    monkeypatch.setattr(hdmi.subprocess, "check_output", lambda *a, **k: edid_output)

    name = hdmi._read_monitor_name("/tmp/edid")  # pylint: disable=protected-access
    assert name == "Preferred Name"


def test_read_monitor_name_fallback_to_vendor(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    edid_output = """
Manufacturer: 'ACME'
Model: 'ZX-1'
"""

    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: True)
    monkeypatch.setattr(hdmi.subprocess, "check_output", lambda *a, **k: edid_output)

    name = hdmi._read_monitor_name("/tmp/edid")  # pylint: disable=protected-access
    assert name == "ACME ZX-1"


def test_max_resolution_from_modes():
    hdmi = importlib.import_module("hdmi")
    modes = [{"res": "1280x720"}, {"res": "3840x2160"}, {"res": "1920x1080"}]
    assert hdmi._max_resolution_from_modes(modes) == "3840x2160"  # pylint: disable=protected-access


def test_get_monitor_info(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(
        hdmi, "_parse_modetest_modes", lambda: [{"res": "3840x2160"}]
    )  # pylint: disable=protected-access
    monkeypatch.setattr(
        hdmi, "_read_monitor_name", lambda _p=None: "Demo Panel"
    )  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi, "_read_current_resolution", lambda: "1920x1080")  # pylint: disable=protected-access

    info = hdmi.get_monitor_info()
    assert info == "Demo Panel (max: 3840x2160, current: 1920x1080)"


def test_get_monitor_info_no_monitor(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_parse_modetest_modes", lambda: [])  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi, "_read_monitor_name", lambda _p=None: "")  # pylint: disable=protected-access

    info = hdmi.get_monitor_info()
    assert info == "No monitor detected"


def test_read_current_resolution(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_run_modetest_full", lambda: MODETEST_WITH_CRTC_SAMPLE)  # pylint: disable=protected-access

    assert hdmi._read_current_resolution() == "1280x720"  # pylint: disable=protected-access


def test_read_monitor_name_missing_file(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: False)

    assert hdmi._read_monitor_name("/does/not/exist") == ""  # pylint: disable=protected-access


def test_read_monitor_name_decode_failure(monkeypatch):
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi.os.path, "exists", lambda path: True)

    def fake_decode(*_a, **_k):
        raise FileNotFoundError

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_decode)
    assert hdmi._read_monitor_name("/tmp/edid") == ""  # pylint: disable=protected-access


def test_max_resolution_handles_invalid_entries():
    hdmi = importlib.import_module("hdmi")
    modes = [{"res": "bad"}, {"res": "640xa"}, {}]
    assert hdmi._max_resolution_from_modes(modes) == ""  # pylint: disable=protected-access
