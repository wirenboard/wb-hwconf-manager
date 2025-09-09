import importlib
import sys
from typing import List


XRANDR_SAMPLE = """
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 160mm x 90mm
   3840x2160     60.00*+ 50.00 30.00
   2560x1440     59.95
DP-1 disconnected (normal left inverted right x axis y axis)
""".strip()


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


def test_parse_xrandr_modes_basic(monkeypatch):
    """Parses xrandr --query output into a resolution->rates mapping."""
    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args[:2] == ["xrandr", "--query"]:
            return XRANDR_SAMPLE
        raise FileNotFoundError

    monkeypatch.setenv("DISPLAY", ":0.0")
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)

    out = hdmi._parse_xrandr_modes("HDMI-1")  # pylint: disable=protected-access
    assert out == {"3840x2160": ["60.00", "50.00", "30.00"], "2560x1440": ["59.95"]}


def test_parse_xrandr_modes_fallback_to_modetest(monkeypatch):
    """Falls back to EDID-derived resolutions when xrandr is unavailable."""
    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args[:2] == ["xrandr", "--query"]:
            raise FileNotFoundError
        return ""

    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi, "_run_modetest", lambda: MODETEST_SAMPLE)  # pylint: disable=protected-access

    out = hdmi._parse_xrandr_modes("HDMI-1")  # pylint: disable=protected-access
    # Fallback returns unique resolutions with empty rate lists
    assert set(out.keys()) == {"3840x2160", "2560x1440"}
    for v in out.values():
        assert isinstance(v, list)


def test_main_listing_format(monkeypatch, capsys):
    """Lists simplified CLI output: '0 - auto' and flat entries without headers."""
    entries: List[dict] = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "xrandr", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {"kind": "xrandr", "title": "3840x2160", "name": "3840x2160", "payload": ""},
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
    assert any(
        ("3840x2160-60.00 (EDID" in line) or ("VESA CVT" in line)
        for line in out
    )


def test_apply_by_index_xrandr(monkeypatch):
    """Applies an xrandr mode by index via 'xrandr --mode WxH'."""
    # Build entries: one xrandr and one detailed
    entries = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "xrandr", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {
            "kind": "edid",
            "title": "1920x1080-60.00 (EDID - 148.50MHz)",
            "name": "1920x1080-60.00",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]
    calls = []

    def fake_run(args, check=False, stdout=None, stderr=None):  # pylint: disable=unused-argument
        calls.append(args)

    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi.subprocess, "run", fake_run)

    rc = hdmi._apply_by_index("1")  # pylint: disable=protected-access
    assert rc == 0
    # Should invoke xrandr --mode for the resolution
    assert any(
        cmd[:3] == ["xrandr", "--output", "HDMI-1"] and cmd[3:5] == ["--mode", "1920x1080"]
        for cmd in calls
    )


def test_apply_by_index_detailed(monkeypatch):
    """Ensures detailed EDID mode presence and applies it by quoted name."""
    # Build entries: one xrandr and one detailed
    entries = [
        {"kind": "auto", "title": "Auto from EDID", "payload": ""},
        {"kind": "xrandr", "title": "1920x1080", "name": "1920x1080", "payload": ""},
        {
            "kind": "edid",
            "title": "1920x1080-60.00 (EDID - 148.50MHz)",
            "name": "1920x1080-60.00",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]

    added = {"ensure": []}
    calls = []

    def fake_run(args, check=False, stdout=None, stderr=None):  # pylint: disable=unused-argument
        calls.append(args)

    def fake_ensure(output, mode_name, payload):
        added["ensure"].append((output, mode_name, payload))

    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi, "_ensure_mode_present", fake_ensure)
    monkeypatch.setattr(hdmi.subprocess, "run", fake_run)

    rc = hdmi._apply_by_index("2")  # pylint: disable=protected-access
    assert rc == 0
    # Ensure mode was prepared and xrandr invoked by name
    assert added["ensure"] and added["ensure"][0][1] == "1920x1080-60.00"
    assert any(
        cmd[:3] == ["xrandr", "--output", "HDMI-1"] and cmd[3:5] == ["--mode", "1920x1080-60.00"]
        for cmd in calls
    )


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
        {"kind": "xrandr", "value": "1920x1080", "title": "1920x1080"},
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
    # Includes xrandr and detailed entries
    assert "1920x1080" in values
    assert "1920x1080-60.00|EDID:148500" in values
    assert "1920x1080-60.00|CVT:173000" in values


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


def test_ensure_mode_present_exists(monkeypatch):
    """Does nothing when the mode already exists in xrandr output."""
    hdmi = importlib.import_module("hdmi")
    mode_name = "1920x1080-60.00"

    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args and args[0] == "xrandr":
            return f"...\n{mode_name} 148.50*\n"
        return ""

    calls = []

    def fake_run(args, check=False, stdout=None, stderr=None):  # pylint: disable=unused-argument
        calls.append(args)

    monkeypatch.setenv("DISPLAY", ":0.0")
    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi.subprocess, "run", fake_run)

    hdmi._ensure_mode_present(  # pylint: disable=protected-access
        "HDMI-1",
        mode_name,
        '"x" 1 2 3 4 5 6 7 8 +hsync +vsync',
    )
    assert not calls  # nothing to add when mode already exists


def test_ensure_mode_present_new(monkeypatch):
    """Creates a new mode and adds it to the output when it does not exist."""
    hdmi = importlib.import_module("hdmi")
    mode_name = "1920x1080-60.00"
    payload = '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync'

    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args and args[0] == "xrandr":
            return ""  # mode not present
        return ""

    calls = []

    def fake_run(args, check=False, stdout=None, stderr=None):  # pylint: disable=unused-argument
        calls.append(args)

    monkeypatch.setenv("DISPLAY", ":0.0")
    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi.subprocess, "run", fake_run)

    hdmi._ensure_mode_present("HDMI-1", mode_name, payload)  # pylint: disable=protected-access
    # Expect two calls: --newmode and --addmode
    assert len(calls) == 2
    assert calls[0][:3] == ["xrandr", "--newmode", mode_name]
    assert calls[1] == ["xrandr", "--addmode", "HDMI-1", mode_name]


def test_apply_by_index_auto(monkeypatch, capsys):
    """Index 0 triggers xrandr --auto and prints the Auto Modeline payload."""
    hdmi = importlib.import_module("hdmi")
    entries = [
        {
            "kind": "auto",
            "title": "Auto from EDID",
            "payload": '"1920x1080-60.00" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync',
        },
    ]

    calls = []

    def fake_run(args, check=False, stdout=None, stderr=None):  # pylint: disable=unused-argument
        calls.append(args)

    monkeypatch.setenv("DISPLAY", ":0.0")
    monkeypatch.setattr(hdmi, "_build_grouped_entries", lambda: entries)  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi.subprocess, "run", fake_run)

    rc = hdmi._apply_by_index("0")  # pylint: disable=protected-access
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith('"1920x1080-60.00" 148.50')
    assert any(cmd[:3] == ["xrandr", "--output", "HDMI-1"] and cmd[3] == "--auto" for cmd in calls)


def test_build_grouped_entries_aggregates(monkeypatch):
    """Aggregates Auto, xrandr resolutions, and detailed EDID/CVT entries (>=2.5K width)."""
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

    # xrandr offers two resolutions
    monkeypatch.setattr(
        hdmi,
        "_parse_xrandr_modes",
        lambda _o: {"1920x1080": ["60.00"], "3840x2160": ["60.00"]},
    )  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi, "_parse_modetest_modes", lambda: modetest_modes)  # pylint: disable=protected-access
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

    # Next, xrandr entries should include 3840x2160 and 1920x1080
    xr = [e for e in entries if e.get("kind") == "xrandr"]
    xr_values = {e["value"] for e in xr}
    assert {"3840x2160", "1920x1080"}.issubset(xr_values)

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


def test_parse_xrandr_modes_no_tools(monkeypatch):
    """Returns an empty mapping when both xrandr and modetest are unavailable."""
    hdmi = importlib.import_module("hdmi")

    def fake_check_output(args, text=False, stderr=None):  # pylint: disable=unused-argument
        if args[:2] == ["xrandr", "--query"]:
            raise FileNotFoundError
        return ""

    monkeypatch.setattr(hdmi.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(hdmi, "_run_modetest", lambda: "")  # pylint: disable=protected-access

    out = hdmi._parse_xrandr_modes("HDMI-1")  # pylint: disable=protected-access
    assert out == {}


def test_build_grouped_entries_no_tools(monkeypatch):
    """With no xrandr or modetest, returns only the Auto entry with empty payload."""
    hdmi = importlib.import_module("hdmi")
    monkeypatch.setattr(hdmi, "_parse_modetest_modes", lambda: [])  # pylint: disable=protected-access
    monkeypatch.setattr(hdmi, "_parse_xrandr_modes", lambda _o: {})  # pylint: disable=protected-access

    entries = hdmi._build_grouped_entries()  # pylint: disable=protected-access
    assert len(entries) == 1
    assert entries[0]["kind"] == "auto"
    assert entries[0]["payload"] == ""


# test_get_hdmi_modes_installed_only_auto was removed: Auto may be present in UI list
