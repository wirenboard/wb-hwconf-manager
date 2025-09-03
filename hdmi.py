#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from typing import Dict, List, Tuple


def _run_modetest() -> str:
    """Return stdout of `modetest -M sun4i-drm -c` or an empty string.

    Used as the single authoritative source for EDID/CTA timings and preferred mode.
    """
    try:
        return subprocess.check_output(["modetest", "-M", "sun4i-drm", "-c"], text=True)
    except Exception:
        return ""


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
            continue
        s = line.strip()
        if not s:
            break
        if s.startswith("index"):
            continue
        if s.startswith("#"):
            m = re.match(
                r"#(\d+)\s+(\d+x\d+)\s+([0-9.]+)\s+"
                r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"
                r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+"
                r"(\d+)\s+flags:\s+([^;]+);",
                s,
            )
            if not m:
                continue
            idx = int(m.group(1))
            name = m.group(2)
            refresh = m.group(3)
            hdisp, hss, hse, htot = map(int, m.group(4, 5, 6, 7))
            vdisp, vss, vse, vtot = map(int, m.group(8, 9, 10, 11))
            pclk_khz = int(m.group(12))
            flags_str = m.group(13)
            ph = "+hsync" if "phsync" in flags_str else "-hsync"
            pv = "+vsync" if "pvsync" in flags_str else "-vsync"
            modes.append(
                {
                    "idx": idx,
                    "res": name,
                    "refresh": refresh,
                    "hdisp": hdisp,
                    "hss": hss,
                    "hse": hse,
                    "htot": htot,
                    "vdisp": vdisp,
                    "vss": vss,
                    "vse": vse,
                    "vtot": vtot,
                    "pclk_khz": pclk_khz,
                    "hs": ph,
                    "vs": pv,
                }
            )
        else:
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
    except Exception:
        return ""
    try:
        out = subprocess.check_output(["cvt", w, h, refresh], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Modeline "):
            return line[len("Modeline "):]
    return ""


def _strip_name_from_modeline_payload(payload: str) -> str:
    """Remove the leading quoted mode name from a Modeline payload string."""
    if not payload:
        return payload
    parts = payload.split(" ", 1)
    if len(parts) == 2 and parts[0].startswith('"'):
        return parts[1]
    return payload


def _parse_xrandr_modes(output_name: str = "HDMI-1") -> Dict[str, List[str]]:
    """Collect available resolutions and their refresh rates from `xrandr --query`.

    Returns a mapping {"WxH": ["RR", ...]}. Entries added via --newmode are skipped.
    """
    modes: Dict[str, List[str]] = {}
    os.environ.setdefault("DISPLAY", ":0.0")
    try:
        txt = subprocess.check_output(["xrandr", "--query"], text=True)
    except Exception:
        return modes
    in_output = False
    for line in txt.splitlines():
        if not in_output:
            if line.startswith(output_name + " ") and (" connected" in line or " connected " in line):
                in_output = True
            continue
        if in_output and line and not line.startswith(" "):
            break
        s = line.strip()
        if not s:
            continue
        first = s.split()[0]
        if "-" in first or "x" not in first:
            continue
        res = first
        rates: List[str] = []
        tail = s[len(first) :].strip()
        for tok in tail.split():
            rt = tok.strip()
            if "x" in rt:
                break
            while rt and (not (rt[-1].isdigit() or rt[-1] == '.')):
                rt = rt[:-1]
            if not rt or not (rt[0].isdigit()):
                continue
            rates.append(rt)
        if rates:
            modes[res] = rates
    return modes


def _build_grouped_entries() -> List[Dict[str, object]]:
    """Build grouped entries for CLI and Web UI.

    Groups consist of:
      - one Auto entry (preferred EDID)
      - XRANDR resolutions without rates
      - detailed EDID/CVT for resolutions >= 2560px width, grouped by "WxH-RR"
        with all EDID variants followed by one unique CVT (if different).

    Returns a flat list of dicts with keys: kind, value, title, name, payload,
    and for detailed entries also w, h, r.
    """
    entries: List[Dict[str, object]] = []
    modes = _parse_modetest_modes()
    # Auto from EDID (preferred proxy: first mode)
    preferred = modes[0] if modes else None
    if preferred:
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
            {"kind": "auto", "value": "auto", "title": "Auto from EDID", "name": "", "payload": ""}
        )

    # xrandr resolutions (no rates), sorted desc
    xr = _parse_xrandr_modes("HDMI-1")
    def res_key(res: str) -> Tuple[int, int]:
        try:
            w, h = map(int, res.split("x"))
        except Exception:
            return (0, 0)
        return (w, h)

    for res in sorted(xr.keys(), key=res_key, reverse=True):
        entries.append({"kind": "xrandr", "value": res, "title": res, "name": res, "payload": ""})

    # Detailed EDID/CVT for ≥ 2560 width (grouped by WxH-RR)
    grouped: Dict[str, Dict[str, object]] = {}
    for m in modes:
        try:
            w, h = map(int, str(m["res"]).split("x"))
        except Exception:
            continue
        if w < 2560:
            continue
        name = f"{m['res']}-{m['refresh']}"
        if name not in grouped:
            grouped[name] = {"w": w, "h": h, "r": float(m["refresh"]), "edids": [], "res": m["res"], "refresh": str(m["refresh"]) }
        grouped[name]["edids"].append({
            "payload": _modeline_from_mode(m),
            "pclk_khz": int(m["pclk_khz"]),
        })

    detail: List[Dict[str, object]] = []
    for name, info in grouped.items():
        w = int(info["w"])
        h = int(info["h"])
        rr = info["r"]
        edids = sorted(info["edids"], key=lambda e: e["pclk_khz"])
        edid_tails = set()
        for e in edids:
            edid_payload = e["payload"]
            edid_tail = _strip_name_from_modeline_payload(edid_payload)
            edid_tails.add(edid_tail)
            edid_mhz_str = f"{(e['pclk_khz']/1000.0):.2f}".rstrip('0').rstrip('.')
            detail.append({
                "kind": "edid",
                "value": f"{name}|EDID:{e['pclk_khz']}",
                "title": f"{name} (EDID - {edid_mhz_str}Mhz)",
                "payload": edid_payload,
                "name": name,
                "w": w,
                "h": h,
                "r": rr,
            })
        # One CVT per name, if unique vs EDID tails
        cvt_tail = _strip_name_from_modeline_payload(_cvt_modeline(info["res"], info["refresh"]))
        if cvt_tail and cvt_tail not in edid_tails:
            cvt_pclk_mhz = cvt_tail.split()[0]
            try:
                cvt_khz = int(round(float(cvt_pclk_mhz) * 1000))
            except Exception:
                cvt_khz = 0
            detail.append({
                "kind": "cvt",
                "value": f"{name}|CVT:{cvt_khz}",
                "title": f"{name} (VESA CVT - {cvt_pclk_mhz}Mhz)",
                "payload": f'"{name}" {cvt_tail}',
                "name": name,
                "w": w,
                "h": h,
                "r": rr,
            })
    detail.sort(key=lambda e: (e["w"], e["h"], e["r"]), reverse=True)
    entries.extend(detail)
    return entries


def get_hdmi_modes() -> List[Dict[str, str]]:
    """Return modes for the Web UI combobox.

    Includes XRANDR resolutions (no rate) and detailed >2K EDID/CVT entries with
    unique values (value suffix encodes the timing source and pixel clock).
    Auto entry is intentionally excluded; the schema supplies it.
    """
    entries = _build_grouped_entries()
    out: List[Dict[str, str]] = []
    for e in entries:
        if e.get("kind") == "auto":
            continue
        out.append({"value": str(e["value"]), "title": str(e["title"])})
    return out


def _modeline_from_mode(m: Dict[str, object]) -> str:
    """Compose a Modeline payload string from a parsed modetest timing dict."""
    name = f"\"{m['res']}-{m['refresh']}\""
    pclk_mhz = float(m["pclk_khz"]) / 1000.0
    pclk_str = ("%.2f" % pclk_mhz).rstrip("0").rstrip(".")
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
        out = subprocess.check_output(["xrandr"], text=True)
    except Exception:
        out = ""
    if mode_name in out:
        return
    parts = modeline_payload.split()
    if not parts:
        return
    name_quoted = parts[0]
    rest = parts[1:]
    subprocess.run(["xrandr", "--newmode", name_quoted.strip('"')] + rest, check=False)
    subprocess.run(["xrandr", "--addmode", output, mode_name], check=False)


def _apply_by_index(index_str: str, output: str = "HDMI-1") -> int:
    """Apply an entry selected by its printed index.

    0 selects Auto (xrandr --auto). Positive indices map to the printed list
    order: XRANDR resolutions first, then detailed EDID/CVT. Prints the Modeline
    for detailed entries. Returns a shell-like exit code (0 on success).
    """
    entries = _build_grouped_entries()
    try:
        idx = int(index_str)
    except Exception:
        print("Invalid index", file=sys.stderr)
        return 2
    if idx == 0:
        os.environ.setdefault("DISPLAY", ":0.0")
        subprocess.run(["xrandr", "--output", output, "--auto"], check=False)
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
        subprocess.run(["xrandr", "--output", output, "--mode", res], check=False)
        return 0
    # detailed edid/cvt
    ml = str(e["payload"])  # full Modeline
    name = str(e["name"])  # WxH-RR
    _ensure_mode_present(output, name, ml)
    print(ml)
    subprocess.run(["xrandr", "--output", output, "--mode", name], check=False)
    return 0


def main() -> int:
    """CLI entry point.

    With no args: prints grouped list with index 0 for Auto from EDID.
    With a single numeric arg: applies the chosen entry.
    """
    if len(sys.argv) == 1:
        print("0 - Auto from EDID")
        entries = _build_grouped_entries()
        i = 1
        print("2) xrandr resolutions (no rate)")
        for e in entries:
            if e.get("kind") == "xrandr":
                print(f"{i} - {e['title']}")
                i += 1
        print("3) Detailed >2K (EDID/CVT)")
        for e in entries:
            if e.get("kind") in {"edid", "cvt"}:
                print(f"{i} - {e['title']}")
                i += 1
        return 0
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        return _apply_by_index(sys.argv[1])
    print(
        "Usage:\n  hdmi.py            # list modes (0 for Auto)\n  hdmi.py <index>    # apply mode by number and print Modeline",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
