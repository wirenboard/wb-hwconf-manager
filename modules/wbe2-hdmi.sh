#!/bin/bash
source "$DATADIR/modules/utils.sh"

XORG_CONFIG_PATH="/etc/X11/xorg.conf.d/10-monitor.conf"
XINIT_SERVICE="xinit.service"
SWAY_PACKAGE="wb-sway-kiosk"
SWAY_SERVICE="wb-sway-kiosk.service"

_run_systemctl() {
	systemctl "$@" >/dev/null 2>&1 || true
}

_run_systemctl_async() {
	systemctl --no-block "$@" >/dev/null 2>&1 || true
}

_is_installed() {
	local package=$1

	dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"
}

_use_legacy_xorg() {
	_is_installed "wb-hdmi"
}

_use_sway_runtime() {
	_is_installed "$SWAY_PACKAGE"
}

_config_mode_to_xorg() {
	local mode=$1
	local base

	if [[ -z "$mode" || "$mode" == "auto" || "$mode" == "null" ]]; then
		return 0
	fi

	base="${mode%%|*}"
	if [[ "$base" == *-* ]]; then
		echo "${base%-*}"
		return 0
	fi

	echo "$base"
}

_config_rotate_to_xorg() {
	case "$1" in
		90)
			echo "right"
			;;
		180)
			echo "inverted"
			;;
		270)
			echo "left"
			;;
		*)
			echo "normal"
			;;
	esac
}

_config_rotate_to_xorg_touch_matrix() {
	case "$1" in
		90)
			echo "0 1 0 -1 0 1 0 0 1"
			;;
		180)
			echo "-1 0 1 0 -1 1 0 0 1"
			;;
		270)
			echo "0 -1 1 1 0 0 0 0 1"
			;;
		*)
			echo "1 0 0 0 1 0 0 0 1"
			;;
	esac
}

_generate_xorg_config() {
	local mode rotate xorg_mode xrotate touch_matrix

	mode="$(config_module_option ".mode")"
	rotate="$(config_module_option ".rotate")"

	xorg_mode="$(_config_mode_to_xorg "$mode")"
	xrotate="$(_config_rotate_to_xorg "$rotate")"
	touch_matrix="$(_config_rotate_to_xorg_touch_matrix "$rotate")"

	mkdir -p "$(dirname "$XORG_CONFIG_PATH")"

	{
		echo 'Section "Monitor"'
		echo '    Identifier "HDMI-1"'
		if [[ -n "$xorg_mode" ]]; then
			echo "    Option \"PreferredMode\" \"$xorg_mode\""
		fi
		echo "    Option \"Rotate\" \"$xrotate\""
		echo 'EndSection'
		echo
		echo 'Section "InputClass"'
		echo '    Identifier "WB HDMI touchscreen calibration"'
		echo '    MatchIsTouchscreen "on"'
		echo '    Driver "libinput"'
		echo "    Option \"CalibrationMatrix\" \"$touch_matrix\""
		echo 'EndSection'
	} > "$XORG_CONFIG_PATH"
}

_cleanup_runtime_artifacts() {
	rm -f "$XORG_CONFIG_PATH"
}

_restart_sway_stack() {
	_run_systemctl stop "$XINIT_SERVICE"
	_run_systemctl_async restart "$SWAY_SERVICE"
}

_restart_xorg_stack() {
	_run_systemctl stop "$SWAY_SERVICE"
	_run_systemctl_async restart "$XINIT_SERVICE"
}

hook_module_add() {
	if _use_legacy_xorg; then
		_generate_xorg_config
		return 0
	fi

	_cleanup_runtime_artifacts
}

hook_module_init() {
	if _use_legacy_xorg; then
		_generate_xorg_config
		_run_systemctl disable "$SWAY_SERVICE"
		_run_systemctl enable "$XINIT_SERVICE"
		_restart_xorg_stack
		return 0
	fi

	if ! _use_sway_runtime; then
		_run_systemctl stop "$SWAY_SERVICE" "$XINIT_SERVICE"
		_run_systemctl disable "$SWAY_SERVICE" "$XINIT_SERVICE"
		_cleanup_runtime_artifacts
		return 0
	fi

	_cleanup_runtime_artifacts
	_run_systemctl disable "$XINIT_SERVICE"
	_run_systemctl enable "$SWAY_SERVICE"
	_restart_sway_stack
}

hook_module_deinit() {
	_run_systemctl stop "$SWAY_SERVICE" "$XINIT_SERVICE"
	_run_systemctl disable "$SWAY_SERVICE" "$XINIT_SERVICE"
	_cleanup_runtime_artifacts
}
