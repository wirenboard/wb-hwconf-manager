source "$DATADIR/modules/utils.sh"

wbec_gpio_base() {
	local chip
	for chip in /sys/class/gpio/gpiochip*; do
		if [[ -r "$chip/device/of_node/compatible" ]]; then
			if tr '\000' '\n' < "$chip/device/of_node/compatible" | grep -qx "wirenboard,wbec-gpio"; then
				cat "$chip/base"
				return 0
			fi
		fi
		if [[ -r "$chip/label" ]] && [[ "$(cat "$chip/label")" = "wbec-gpio" ]]; then
			cat "$chip/base"
			return 0
		fi
	done
	return 1
}

resolve_rts_gpio() {
	local offset="$1"
	local slot_suffix="${SLOT##*-}"

	if [[ -z "$offset" ]]; then
		echo "ERROR: GPIO_RTS is not defined for slot $SLOT"
		return 1
	fi

	case "$slot_suffix" in
		mod1|mod2)
			local base
			base="$(wbec_gpio_base)" || return 1
			echo $((base + offset))
			;;
		*)
			echo "$offset"
			;;
	esac
}

slot_can_dt_path() {
	local slot_def
	slot_def="$(slot_get_filename "$SLOT")" || return 1

	local alias
	alias="$(awk '/^[[:space:]]*#define[[:space:]]+SLOT_UART_ALIAS[[:space:]]+/ {print $3; exit}' "$slot_def")"
	alias="${alias#&}"
	[[ -n "$alias" ]] || return 1

	local symbol="/proc/device-tree/__symbols__/${alias}"
	if [[ -r "$symbol" ]]; then
		local uart_path
		uart_path="$(tr -d '\0' < "$symbol")"
		[[ -n "$uart_path" ]] || return 1
		echo "${uart_path}/can@0"
		return 0
	fi

	return 1
}

slot_can_ifaces() {
	local can_path
	can_path="$(slot_can_dt_path)" || return 1

	local target="/sys/firmware/devicetree/base${can_path}"
	local found=1
	local net
	for net in /sys/class/net/can*; do
		[[ -e "$net" ]] || continue
		[[ -e "$net/device/of_node" ]] || continue
		if [[ "$(readlink -f "$net/device/of_node")" != "$target" ]]; then
			continue
		fi
		echo "${net##*/}"
		found=0
	done
	return $found
}

slot_can_down() {
	command -v ip >/dev/null 2>&1 || return 0

	local iface
	for iface in $(slot_can_ifaces); do
		ip link set "$iface" down >/dev/null 2>&1 || true
	done
}

slot_can_unbind() {
	local iface
	for iface in $(slot_can_ifaces); do
		local dev_path
		dev_path="$(readlink -f "/sys/class/net/${iface}/device")" || continue
		local unbind="${dev_path}/driver/unbind"
		[[ -w "$unbind" ]] || continue
		echo "${dev_path##*/}" > "$unbind" 2>/dev/null || true
	done
}

slot_can_wait_detach() {
	local i
	for ((i=0; i<10; i++)); do
		slot_can_ifaces >/dev/null || return 0
		sleep 0.2
	done
}

slot_can_target_name() {
	local slot_suffix="${SLOT##*-}"
	case "$slot_suffix" in
		mod[1-4])
			echo "canMOD${slot_suffix#mod}"
			;;
		*)
			return 1
			;;
	esac
}

slot_can_rename() {
	command -v ip >/dev/null 2>&1 || return 0

	local target
	target="$(slot_can_target_name)" || return 0

	local iface
	local i
	for ((i=0; i<10; i++)); do
		for iface in $(slot_can_ifaces); do
			[[ "$iface" == "$target" ]] && return 0
			ip link set "$iface" down >/dev/null 2>&1 || true
			ip link set "$iface" name "$target" >/dev/null 2>&1 || true
			return 0
		done
		sleep 0.2
	done
}

slot_can_nm_unmanage() {
	command -v nmcli >/dev/null 2>&1 || return 0

	local iface
	for iface in $(slot_can_ifaces); do
		nmcli dev set "$iface" managed no >/dev/null 2>&1 || true
	done
}

slot_can_apply_settings() {
	command -v ip >/dev/null 2>&1 || return 0

	local auto_up
	auto_up="$(config_module_option ".autoUp // false")"
	[[ "$auto_up" == "true" ]] || return 0

	local bitrate
	bitrate="$(config_module_option ".bitrate // 125000")"
	local listen_only
	listen_only="$(config_module_option ".listenOnly // false")"
	local loopback
	loopback="$(config_module_option ".loopback // false")"
	local restart_ms
	restart_ms="$(config_module_option ".restartMs // 0")"

	local args=(type can bitrate "$bitrate")
	if [[ "$listen_only" == "true" ]]; then
		args+=(listen-only on)
	else
		args+=(listen-only off)
	fi
	if [[ "$loopback" == "true" ]]; then
		args+=(loopback on)
	else
		args+=(loopback off)
	fi
	if [[ "$restart_ms" =~ ^[0-9]+$ ]]; then
		args+=(restart-ms "$restart_ms")
	fi

	local iface
	for iface in $(slot_can_ifaces); do
		ip link set "$iface" down >/dev/null 2>&1 || true
		ip link set "$iface" "${args[@]}" >/dev/null 2>&1 || true
		ip link set "$iface" up >/dev/null 2>&1 || true
	done
}

hook_module_init() {
	local rts_gpio
	rts_gpio="$(resolve_rts_gpio "$GPIO_RTS")" || {
		echo "ERROR: wbec gpiochip not found"
		return 1
	}

	sysfs_gpio_export $rts_gpio
	sysfs_gpio_direction $rts_gpio out

	local term_mode="$(config_module_option ".terminatorsMode")"
	if [ "$term_mode" = "disabled" ]
	then
		echo "terminators are disabled"
		sysfs_gpio_set $rts_gpio 0
	else
		echo "terminators are enabled"
		sysfs_gpio_set $rts_gpio 1
	fi

	slot_can_rename
	slot_can_nm_unmanage
	slot_can_apply_settings
}

hook_module_deinit() {
	local rts_gpio
	rts_gpio="$(resolve_rts_gpio "$GPIO_RTS")" || return 0

	slot_can_down
	slot_can_unbind
	slot_can_wait_detach

	if [[ ! -e "${SYSFS_GPIO}/gpio${rts_gpio}" ]]; then
		return 0
	fi

	sysfs_gpio_direction $rts_gpio in
	sysfs_gpio_unexport $rts_gpio
}
