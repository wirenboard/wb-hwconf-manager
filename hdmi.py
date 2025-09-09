#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from typing import List, Dict, Optional, Tuple


def _run_modetest() -> str:
    """Return stdout of `modetest -M sun4i-drm -c` or an empty string.

    Used as the single authoritative source for EDID/CTA timings and preferred mode.
    """
    try:
        return subprocess.check_output(["modetest", "-M", "sun4i-drm", "-c"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


# Precompiled mode line pattern from modetest
_MODE_LINE_RE = re.compile(
    r"#(?P<idx>\d+)\s+(?P<name>\d+x\d+)\s+(?P<refresh>[0-9.]+)\s+"
    r"(?P<hdisp>\d+)\s+(?P<hss>\d+)\s+(?P<hse>\d+)\s+(?P<htot>\d+)\s+"
    r"(?P<vdisp>\d+)\s+(?P<vss>\d+)\s+(?P<vse>\d+)\s+(?P<vtot>\d+)\s+"
    r"(?P<pclk_khz>\d+)\s+flags:\s+(?P<flags>[^;]+);"
)


def _parse_flags(flags_str: str) -> Tuple[str, str]:
    """Return ('+hsync'|'-hsync', '+vsync'|'-vsync') from modetest flags string."""
    # modetest outputs 'phsync'/'pvsync' for positive; otherwise treat as negative.
    ph = "+hsync" if "phsync" in flags_str else "-hsync"
    pv = "+vsync" if "pvsync" in flags_str else "-vsync"
    return ph, pv


def _parse_mode_line(s: str) -> Optional[Dict[str, object]]:
    """Parse a single modetest mode line into a timing dict or None."""
    m = _MODE_LINE_RE.match(s)
    if not m:
        return None

    g = m.groupdict()
    ph, pv = _parse_flags(g["flags"])

    return {
        "idx": int(g["idx"]),
        "res": g["name"],
        "refresh": g["refresh"],
        "hdisp": int(g["hdisp"]),
        "hss": int(g["hss"]),
        "hse": int(g["hse"]),
        "htot": int(g["htot"]),
        "vdisp": int(g["vdisp"]),
        "vss": int(g["vss"]),
        "vse": int(g["vse"]),
        "vtot": int(g["vtot"]),
        "pclk_khz": int(g["pclk_khz"]),
        "hs": ph,
        "vs": pv,
    }


def _parse_modetest_modes() -> List[Dict[str, object]]:
    """Parse modetest output into a list of timing dicts.

    Each item contains: idx, res ("WxH"), refresh (str), hdisp/hss/hse/htot,
    vdisp/vss/vse/vtot, pclk_khz (int), and sync polarities (hs, vs).
    """
    txt = _run_modetest()
    if not txt:
        return []

    modes: List[Dict[str, object]] = []
    in_connectors = False
    in_modes = False
    connector_ok = False

    for line in txt.splitlines():
        if not in_connectors:
            if line.strip().startswith("Connectors:"):
                in_connectors = True
            continue

        if not in_modes:
            parts = line.split()
            if len(parts) >= 3 and parts[2] == "connected":
                connector_ok = True
                continue
            if connector_ok and line.strip().startswith("modes:"):
                in_modes = True
            continue

        s = line.strip()
        if not s:
            break
        if s.startswith("index"):
            continue
        if s.startswith("#"):
            if (item := _parse_mode_line(s)) is not None:
                modes.append(item)
            continue
        break

    return modes


def _cvt_modeline(res: str, refresh: str) -> str:
    """Generate a VESA CVT Modeline for given resolution and refresh via `cvt`.

    Args:
        res: Resolution in the form "WxH" (e.g., "3840x2160").
        refresh: Refresh rate string (e.g., "60.00").

    Returns:
        Modeline payload without the leading word "Modeline", or an empty string
        when generation fails or `cvt` is not available.
    """
    try:
        w, h = res.split("x")
    except ValueError:
        return ""
    try:
        out = subprocess.check_output(["cvt", w, h, refresh], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Modeline "):
            return line[len("Modeline ") :]
    return ""


def _strip_name_from_modeline_payload(payload: str) -> str:
    """Remove the leading quoted mode name from a Modeline payload string."""
    if not payload:
        return payload
    parts = payload.split(" ", 1)
    if len(parts) == 2 and parts[0].startswith('"'):
        return parts[1]
    return payload


def _tokenize_rates(tail: str) -> List[str]:
    """Extract numeric refresh tokens from a xrandr mode tail string.

    Stops when another resolution-like token appears. Strips trailing non-digit
    characters except dot.
    """
    rates: List[str] = []
    for tok in tail.split():
        rt = tok.strip()
        if "x" in rt:
            break
        while rt and not (rt[-1].isdigit() or rt[-1] == "."):
            rt = rt[:-1]
        if not rt or not rt[0].isdigit():
            continue
        rates.append(rt)
    return rates


def _choose_xrandr_block(blocks: Dict[str, Dict[str, List[str]]], output_name: str) -> Dict[str, List[str]]:
    """Choose a preferred output block.

    Priority: explicit output_name, then any HDMI*, then first by name.
    """
    if output_name in blocks:
        return blocks[output_name]
    for name, sub in blocks.items():
        if name.startswith("HDMI"):
            return sub
    if blocks:
        first_name = sorted(blocks.keys())[0]
        return blocks[first_name]
    return {}


def _parse_xrandr_modes(output_name: str = "HDMI-1") -> Dict[str, List[str]]:
    """Collect available resolutions and their refresh rates from `xrandr --query`.

    Returns a mapping {"WxH": ["RR", ...]}. Entries added via --newmode are skipped.

    If xrandr is unavailable (no DISPLAY or binary missing), gracefully fall back to
    resolutions derived from EDID via modetest, returning unique WxH keys with empty
    rate lists. This preserves the section in CLI and Web UI.
    """

    def _from_modetest_fallback() -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for m in _parse_modetest_modes():
            res = str(m.get("res", ""))
            if res:
                result.setdefault(res, [])
        return result

    os.environ.setdefault("DISPLAY", ":0.0")
    try:
        txt = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return _from_modetest_fallback()

    # Parse only the requested output block. If not found, fall back to first connected.
    blocks: Dict[str, Dict[str, List[str]]] = {}
    current: Optional[str] = None
    for line in txt.splitlines():
        if not line:
            continue
        if not line.startswith(" "):
            # Header line: "<OUTPUT> connected ..." or "<OUTPUT> disconnected"
            current = None
            name = line.split()[0]
            if " connected" in line:
                current = name
                blocks.setdefault(current, {})
            continue
        if not current:
            continue
        s = line.strip()
        if not s:
            continue
        first = s.split()[0]
        # Skip modelines and meta
        if "-" in first or "x" not in first:
            continue
        res = first
        tail = s[len(first) :].strip()
        rates = _tokenize_rates(tail)
        if rates:
            blocks[current].setdefault(res, rates)

    chosen = _choose_xrandr_block(blocks, output_name)
    if chosen:
        return chosen
    return _from_modetest_fallback()


def _make_edid_entry(name: str, info: Dict[str, object], e: Dict[str, object]) -> Dict[str, object]:
    """Format one EDID entry."""
    w = int(info["w"])
    h = int(info["h"])
    rr = float(info["r"])
    payload = e["payload"]
    mhz = f"{(e['pclk_khz']/1000.0):.2f}".rstrip("0").rstrip(".")
    return {
        "kind": "edid",
        "value": f"{name}|EDID:{e['pclk_khz']}",
        "title": f"{name} (EDID - {mhz}MHz)",
        "payload": payload,
        "name": name,
        "w": w,
        "h": h,
        "r": rr,
    }


def _make_cvt_entry(name: str, info: Dict[str, object], tail: str) -> Dict[str, object]:
    """Format one CVT entry."""
    try:
        cvt_khz = int(round(float(tail.split()[0]) * 1000))
    except ValueError:
        cvt_khz = 0
    w = int(info["w"])
    h = int(info["h"])
    rr = float(info["r"])
    return {
        "kind": "cvt",
        "value": f"{name}|CVT:{cvt_khz}",
        "title": f"{name} (VESA CVT - {tail.split()[0]}MHz)",
        "payload": f'"{name}" {tail}',
        "name": name,
        "w": w,
        "h": h,
        "r": rr,
    }


def _build_detailed_entries(modes: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Build detailed EDID/CVT entries for modes with width >= 2560."""
    grouped: Dict[str, Dict[str, object]] = {}
    for m in modes:
        try:
            w, h = map(int, str(m["res"]).split("x"))
        except (ValueError, TypeError):
            continue
        if w < 2560:
            continue
        name = f"{m['res']}-{m['refresh']}"
        if name not in grouped:
            grouped[name] = {
                "w": w,
                "h": h,
                "r": float(m["refresh"]),
                "edids": [],
                "res": m["res"],
                "refresh": str(m["refresh"]),
            }
        grouped[name]["edids"].append({"payload": _modeline_from_mode(m), "pclk_khz": int(m["pclk_khz"])})

    detail: List[Dict[str, object]] = []
    for name, info in grouped.items():
        edids = sorted(info["edids"], key=lambda e: e["pclk_khz"])
        edid_tails = set()
        for e in edids:
            entry = _make_edid_entry(name, info, e)
            detail.append(entry)
            edid_tails.add(_strip_name_from_modeline_payload(e["payload"]))
        cvt_tail = _strip_name_from_modeline_payload(_cvt_modeline(info["res"], info["refresh"]))
        if cvt_tail and cvt_tail not in edid_tails:
            detail.append(_make_cvt_entry(name, info, cvt_tail))
    detail.sort(key=lambda e: (e["w"], e["h"], e["r"]), reverse=True)
    return detail


def _build_grouped_entries() -> List[Dict[str, object]]:
    """Build grouped entries for CLI and Web UI.

    Groups consist of:
      - one Auto entry (preferred EDID)
      - XRANDR resolutions without rates
      - detailed EDID/CVT for resolutions >= 2560px width
    """
    entries: List[Dict[str, object]] = []
    modes = _parse_modetest_modes()

    # Auto entry
    if modes:
        preferred = modes[0]
        entries.append(
            {
                "kind": "auto",
                "value": "auto",
                "title": "Auto from EDID",
                "name": f"{preferred['res']}-{preferred['refresh']}",
                "payload": _modeline_from_mode(preferred),
            }
        )
    else:
        entries.append(
            {
                "kind": "auto",
                "value": "auto",
                "title": "Auto from EDID",
                "name": "",
                "payload": "",
            }
        )

    # XRANDR entries
    xr = _parse_xrandr_modes("HDMI-1")

    def res_key(res: str) -> Tuple[int, int]:
        try:
            w, h = map(int, res.split("x"))
        except (ValueError, TypeError):
            return (0, 0)
        return (w, h)

    for res in sorted(xr.keys(), key=res_key, reverse=True):
        entries.append(
            {
                "kind": "xrandr",
                "value": res,
                "title": res,
                "name": res,
                "payload": "",
            }
        )

    # Detailed EDID/CVT entries
    entries.extend(_build_detailed_entries(modes))

    return entries


def get_hdmi_modes() -> List[Dict[str, str]]:
    """Return modes for the Web UI combobox.

    Includes XRANDR resolutions (no rate) and detailed >2K EDID/CVT entries with
    unique values (value suffix encodes the timing source and pixel clock).
    Auto entry is intentionally excluded; the schema supplies it.
    """
    installed = False
    try:
        out = subprocess.check_output(["dpkg-query", "-W", "-f=${Status}", "wb-hdmi"], text=True)
        installed = "install ok installed" in out
    except (subprocess.CalledProcessError, FileNotFoundError):
        installed = False

    out: List[Dict[str, str]] = []

    if installed:
        entries = _build_grouped_entries()
        for e in entries:
            if e.get("kind") == "auto":
                continue
            out.append({"value": str(e["value"]), "title": str(e["title"])})
    else:
        # Expose a single message in case any UI watches available_hdmi_modes
        msg = "Для работы с графическим интерфейсом необходимо установить пакет wb-hdmi: apt install wb-hdmi"
        out.append({"value": "auto", "title": msg})

    return out


def _modeline_from_mode(m: Dict[str, object]) -> str:
    """Compose a Modeline payload string from a parsed modetest timing dict."""
    name = f"\"{m['res']}-{m['refresh']}\""
    pclk_mhz = float(m["pclk_khz"]) / 1000.0
    pclk_str = f"{pclk_mhz:.2f}".rstrip("0").rstrip(".")
    return (
        f"{name} {pclk_str} {m['hdisp']} {m['hss']} {m['hse']} {m['htot']} "
        f"{m['vdisp']} {m['vss']} {m['vse']} {m['vtot']} {m['hs']} {m['vs']}"
    )


def _ensure_mode_present(output: str, mode_name: str, modeline_payload: str) -> None:
    """Ensure a mode is known to xrandr: create with --newmode and add to output.

    No-op when the mode already exists. Requires X server (uses DISPLAY=:0.0).
    """
    os.environ.setdefault("DISPLAY", ":0.0")
    try:
        out = subprocess.check_output(["xrandr"], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        out = ""
    if mode_name in out:
        return
    parts = modeline_payload.split()
    if not parts:
        return
    name_quoted = parts[0]
    rest = parts[1:]
    subprocess.run(
        ["xrandr", "--newmode", name_quoted.strip('"')] + rest,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["xrandr", "--addmode", output, mode_name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _apply_by_index(index_str: str, output: str = "HDMI-1") -> int:
    """Apply an entry selected by its printed index.

    0 selects Auto (xrandr --auto). Positive indices map to the printed list
    order: XRANDR resolutions first, then detailed EDID/CVT. Prints the Modeline
    for detailed entries. Returns a shell-like exit code (0 on success).
    """
    entries = _build_grouped_entries()
    try:
        idx = int(index_str)
    except ValueError:
        print("Invalid index", file=sys.stderr)
        return 2
    if idx == 0:
        os.environ.setdefault("DISPLAY", ":0.0")
        subprocess.run(
            ["xrandr", "--output", output, "--auto"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if entries and entries[0].get("payload"):
            print(str(entries[0]["payload"]))
        return 0
    # Flatten selection order: xrandr first, then detailed
    filtered: List[Dict[str, object]] = []
    filtered.extend([e for e in entries if e.get("kind") == "xrandr"])
    filtered.extend([e for e in entries if e.get("kind") in {"edid", "cvt"}])
    if idx < 1 or idx > len(filtered):
        print("Index out of range", file=sys.stderr)
        return 2
    e = filtered[idx - 1]
    kind = str(e.get("kind"))
    os.environ.setdefault("DISPLAY", ":0.0")
    if kind == "xrandr":
        res = str(e["name"])  # WxH
        subprocess.run(
            ["xrandr", "--output", output, "--mode", res],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return 0
    # detailed edid/cvt
    ml = str(e["payload"])  # full Modeline
    name = str(e["name"])  # WxH-RR
    _ensure_mode_present(output, name, ml)
    print(ml)
    subprocess.run(
        ["xrandr", "--output", output, "--mode", name],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return 0


def main() -> int:
    """CLI entry point.

    With no args: prints grouped list with index 0 for Auto from EDID.
    With a single numeric arg: applies the chosen entry.
    """
    if len(sys.argv) == 1:
        # Simplified output for easier parsing in shell scripts
        print("0 - auto")
        entries = _build_grouped_entries()
        i = 1
        # xrandr resolutions first
        for e in entries:
            if e.get("kind") == "xrandr":
                print(f"{i} - {e['title']}")
                i += 1
        # detailed EDID/CVT entries next
        for e in entries:
            if e.get("kind") in {"edid", "cvt"}:
                print(f"{i} - {e['title']}")
                i += 1
        return 0
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        return _apply_by_index(sys.argv[1])
    print("Usage:", file=sys.stderr)
    print("  hdmi.py            # list modes (0 for Auto)", file=sys.stderr)
    print("  hdmi.py <index>    # apply mode by number and print Modeline", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
