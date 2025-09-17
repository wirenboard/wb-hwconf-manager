#!/bin/bash
source "$DATADIR/modules/utils.sh"

hook_module_add() {
    local XORG_CONFIG_PATH="/etc/X11/xorg.conf.d/10-monitor.conf"
    local URL_CONFIG_PATH="/root/url"

    # Extract module options via jq
    local mode="$(config_module_option ".mode")"
    local rotate="$(config_module_option ".rotate")"
    local url="$(config_module_option ".url")"

    # Parse mode: may be "WxH-Rate|EDID" / "WxH-Rate|CVT" / "WxH-Rate" / "WxH"
    local res=""
    local rate=""
    local variant=""
    local modeline_name=""
    local modeline_def=""
    if [[ -n "$mode" && "$mode" != "auto" ]]; then
        # Split variant suffix after '|', if present
        if [[ "$mode" == *"|"* ]]; then
            variant="${mode##*|}"
            variant_base="${variant%%:*}"
            variant_extra="${variant#*:}"
            [[ "$variant" == "$variant_base" ]] && variant_extra=""
            mode="${mode%%|*}"
        fi
        if [[ "$mode" == *-* ]]; then
            res="${mode%%-*}"
            rate="${mode##*-}"
        else
            res="$mode"
        fi
    fi

    # Get Modeline via hdmi.py (EDID -> built-in CVT) and remember target index
    if [[ -n "$res" && -n "$rate" ]]; then
        local w="${res%x*}"
        local h="${res#*x}"
        # Find target mode index from hdmi.py list (one mode per line)
        local idx
        if [[ "$variant" == "CVT" ]]; then
            # Match titles starting with "WxH-Rate (VESA CVT..."
            idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v base="${w}x${h}-${rate}" 'index($2, base " (VESA CVT")==1 {print $1; exit}' )
        elif [[ "$variant" == "EDID" ]]; then
            # Match titles starting with "WxH-Rate (EDID ..."
            idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v base="${w}x${h}-${rate}" 'index($2, base " (EDID ")==1 {print $1; exit}' )
        else
            # Generic: strip suffix " ( ... )" and match by base name
            idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v target="${w}x${h}-${rate}" '{t=$2; sub(/ \(.+\)$/,"",t); if(t==target){print $1; exit}}' )
        fi
        # Generate modeline to write into Xorg config
        if [[ -n "$idx" ]]; then
            modeline_def=$(/usr/lib/wb-hwconf-manager/hdmi.py "$idx" 2>/dev/null)
        fi

        # Mode name is the first token (quoted) from modeline_def
        if [[ -n "$modeline_def" ]]; then
            modeline_name=$(sed -E 's/^"([^"]+)".*$/\1/' <<< "$modeline_def")
            # Normalize mode name if needed
            if [[ "$modeline_name" != "${w}x${h}-${rate}" ]]; then
                local norm_name="${w}x${h}-${rate}"
                modeline_def=$(sed -E "s/^\"[^\"]+\"/\"${norm_name}\"/" <<< "$modeline_def")
                modeline_name="$norm_name"
            fi
        fi
    fi

    # Map rotate degrees to X11 value (normal, left, right, inverted)
    case "$rotate" in
        90) xrotate="right" ;;
        180) xrotate="inverted" ;;
        270) xrotate="left" ;;
        *) xrotate="normal" ;;
    esac

    # Generate xorg.conf.d/10-monitor.conf
    mkdir -p "$(dirname "$XORG_CONFIG_PATH")"
    {
        echo 'Section "Monitor"'
        echo '    Identifier "HDMI-1"'
        # If modeline is available — add it and set as preferred
        if [[ -n "$modeline_def" && -n "$modeline_name" ]]; then
            echo "    Modeline $modeline_def"
            echo "    Option \"PreferredMode\" \"$modeline_name\""
        elif [[ -n "$res" ]]; then
            # Fallback: at least set desired resolution
            echo "    Option \"PreferredMode\" \"$res\""
        fi
        echo "    Option \"Rotate\" \"$xrotate\""
        echo 'EndSection'
    } > "$XORG_CONFIG_PATH"

    if [[ -n "$url" ]]; then
        echo "$url" > "$URL_CONFIG_PATH"
    else
        rm "$URL_CONFIG_PATH"
    fi

    # Apply xrandr settings or start xinit
    if pgrep -x xinit > /dev/null; then
        echo "Xinit is running. Applying xrandr settings..."
        export DISPLAY=:0.0

        # If index found — apply mode by number (hdmi.py will add it if needed)
        if [[ -n "$idx" ]]; then
            /usr/lib/wb-hwconf-manager/hdmi.py "$idx" >/dev/null 2>&1 || true
        else
            # Fallback: use xrandr by resolution and rate
            cmd=(xrandr --output HDMI-1)
            if [[ -n "$res" ]]; then
                cmd+=("--mode" "$res")
                [[ -n "$rate" ]] && cmd+=("--rate" "$rate")
            fi
            "${cmd[@]}" || true
        fi

        # Rotate screen
        xrandr --output HDMI-1 --rotate "$xrotate" || true

    else
        systemctl start xinit.service
    fi

}

hook_module_init() {
	systemctl enable xinit.service
	systemctl start xinit.service &
}

hook_module_deinit() {
	systemctl stop xinit.service &
	systemctl disable xinit.service
}
