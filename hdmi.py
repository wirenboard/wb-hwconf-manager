#!/usr/bin/env python3
import glob
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


def _run_modetest() -> str:
    """Return stdout of `modetest -M sun4i-drm -c` or an empty string.

    Used as the single authoritative source for EDID/CTA timings and preferred mode.
    """
    try:
        return subprocess.check_output(["modetest", "-M", "sun4i-drm", "-c"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _run_modetest_full() -> str:
    """Return stdout of full `modetest -M sun4i-drm` or an empty string."""
    try:
        return subprocess.check_output(["modetest", "-M", "sun4i-drm"], text=True)
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


def _read_current_resolution() -> str:  # pylint: disable=too-many-branches
    """Return current active HDMI resolution from modetest CRTC state."""
    txt = _run_modetest_full()
    if not txt:
        return ""

    encoder_to_crtc: Dict[str, str] = {}
    hdmi_encoder = ""
    section = ""

    for raw_line in txt.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("Encoders:"):
            section = "encoders"
            continue
        if stripped.startswith("Connectors:"):
            section = "connectors"
            continue
        if stripped.startswith("CRTCs:"):
            section = "crtcs"
            continue
        if not stripped:
            continue

        if section == "encoders":
            parts = stripped.split()
            if len(parts) >= 2 and parts[0].isdigit():
                encoder_to_crtc[parts[0]] = parts[1]
            continue

        if section == "connectors":
            parts = stripped.split()
            if len(parts) >= 4 and parts[0].isdigit() and parts[1].isdigit():
                if parts[2] == "connected" and parts[3].startswith("HDMI-A-"):
                    hdmi_encoder = parts[1]
                    continue
            continue

        if section == "crtcs" and hdmi_encoder:
            crtc_id = encoder_to_crtc.get(hdmi_encoder, "")
            parts = stripped.split()
            if len(parts) >= 4 and crtc_id and parts[0] == crtc_id:
                size = parts[3].strip("()")
                if size and size != "0x0":
                    return size
                return ""

    return ""


def _clean_monitor_field(text: str) -> str:
    """Trim whitespace/quotes from EDID-decoded strings."""
    return text.replace("'", "").strip()


def _find_connected_hdmi_edid() -> str:
    """Return EDID path for the first connected HDMI connector."""
    for status_path in sorted(glob.glob("/sys/class/drm/card*-HDMI-A-*/status")):
        try:
            with open(status_path, "r", encoding="utf-8") as status_file:
                if status_file.read().strip() != "connected":
                    continue
        except OSError:
            continue

        edid_path = os.path.join(os.path.dirname(status_path), "edid")
        if os.path.exists(edid_path):
            return edid_path

    return ""


def _read_monitor_name(edid_path: Optional[str] = None) -> str:
    """Return monitor name parsed from EDID via edid-decode."""
    if edid_path is None:
        edid_path = _find_connected_hdmi_edid()
    if not os.path.exists(edid_path):
        return ""
    try:
        out = subprocess.check_output(["edid-decode", edid_path], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

    name = ""
    manufacturer = ""
    model = ""

    for raw_line in out.splitlines():
        line = raw_line.strip()
        if line.startswith("Display Product Name:"):
            _, _, value = line.partition(":")
            candidate = _clean_monitor_field(value)
            if candidate:
                name = candidate
                break
        if line.startswith("Monitor name:") and not name:
            _, _, value = line.partition(":")
            candidate = _clean_monitor_field(value)
            if candidate:
                name = candidate
        if line.startswith("Manufacturer:"):
            _, _, value = line.partition(":")
            manufacturer = _clean_monitor_field(value)
        if line.startswith("Model:"):
            _, _, value = line.partition(":")
            model = _clean_monitor_field(value)

    if name:
        return name

    fallback = f"{manufacturer} {model}".strip()
    return fallback


def _max_resolution_from_modes(modes: List[Dict[str, object]]) -> str:
    """Return resolution string with the largest pixel area (ties resolved by refresh)."""
    best_res = ""
    best_pixels = -1

    for mode in modes:
        res = str(mode.get("res", ""))
        if "x" not in res:
            continue
        try:
            width_str, height_str = res.split("x")
            width = int(width_str)
            height = int(height_str)
        except (ValueError, TypeError):
            continue
        pixels = width * height
        if pixels > best_pixels:
            best_pixels = pixels
            best_res = res

    return best_res


def get_monitor_info() -> str:
    """Return basic info about the connected monitor for display in the UI."""
    modes = _parse_modetest_modes()
    max_res = _max_resolution_from_modes(modes)
    current_res = _read_current_resolution()
    name = _read_monitor_name()

    if name:
        details = []
        if max_res:
            details.append(f"max: {max_res}")
        if current_res:
            details.append(f"current: {current_res}")
        if details:
            return f"{name} ({', '.join(details)})"
        return name

    return "No monitor detected"


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


def _build_basic_entries(modes: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Build unique flat resolution entries from modetest data."""
    entries: List[Dict[str, object]] = []
    seen = set()

    def res_key(res: str) -> Tuple[int, int]:
        try:
            w, h = map(int, res.split("x"))
        except (ValueError, TypeError):
            return (0, 0)
        return (w, h)

    unique_modes = sorted(
        {
            str(mode.get("res", ""))
            for mode in modes
            if str(mode.get("res", "")) and "x" in str(mode.get("res", ""))
        },
        key=res_key,
        reverse=True,
    )

    for res in unique_modes:
        if res in seen:
            continue
        seen.add(res)
        entries.append(
            {
                "kind": "mode",
                "value": res,
                "title": res,
                "name": res,
                "payload": "",
            }
        )

    return entries


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
      - flat resolutions from modetest
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
                "title": "AUTO from EDID",
                "name": f"{preferred['res']}-{preferred['refresh']}",
                "payload": _modeline_from_mode(preferred),
            }
        )
    else:
        entries.append(
            {
                "kind": "auto",
                "value": "auto",
                "title": "AUTO from EDID",
                "name": "",
                "payload": "",
            }
        )

    entries.extend(_build_basic_entries(modes))

    # Detailed EDID/CVT entries
    entries.extend(_build_detailed_entries(modes))

    return entries


def get_hdmi_modes() -> List[Dict[str, str]]:
    """Return modes for the Web UI combobox.

    Includes flat modetest resolutions and detailed >2K EDID/CVT entries with
    unique values (value suffix encodes the timing source and pixel clock).
    May include the Auto entry depending on upstream grouping logic.
    """

    def _is_installed(package: str) -> bool:
        try:
            out = subprocess.check_output(["dpkg-query", "-W", "-f=${Status}", package], text=True)
            return "install ok installed" in out
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    installed = _is_installed("wb-hdmi") or _is_installed("wb-hdmi-xorg")

    out: List[Dict[str, str]] = []

    if installed:
        entries = _build_grouped_entries()
        for e in entries:
            out.append({"value": str(e["value"]), "title": str(e["title"])})
    else:
        # Expose a single message in case any UI watches available_hdmi_modes
        msg = (
            "To use the graphical interface, you need to install the "
            "wb-hdmi or wb-hdmi-xorg package: apt install wb-hdmi"
        )
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


def _apply_by_index(index_str: str) -> int:
    """Print a Modeline payload for the selected entry when available.

    0 selects the preferred EDID mode. Positive indices map to the printed list
    order: flat resolutions first, then detailed EDID/CVT entries.
    Returns a shell-like exit code (0 on success).
    """
    entries = _build_grouped_entries()
    try:
        idx = int(index_str)
    except ValueError:
        print("Invalid index", file=sys.stderr)
        return 2
    if idx == 0:
        if entries and entries[0].get("payload"):
            print(str(entries[0]["payload"]))
        return 0
    # Flatten selection order: flat resolutions first, then detailed
    filtered: List[Dict[str, object]] = []
    filtered.extend([e for e in entries if e.get("kind") == "mode"])
    filtered.extend([e for e in entries if e.get("kind") in {"edid", "cvt"}])
    if idx < 1 or idx > len(filtered):
        print("Index out of range", file=sys.stderr)
        return 2
    e = filtered[idx - 1]
    kind = str(e.get("kind"))
    if kind == "mode":
        return 0
    # detailed edid/cvt
    print(str(e["payload"]))
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
        # flat resolutions first
        for e in entries:
            if e.get("kind") == "mode":
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
