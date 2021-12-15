source "$DATADIR/modules/utils.sh"

local GPIO_BASE=224
local GPIO_COUNT=16

hook_module_add() {
	local items=()
	for ((i = 0; i < 8; i++)); do
		items+=( \
			"MZ${SLOT_NUM}_TTL$[i+1]" \
			$[GPIO_BASE+i+8] \
			"input" \
		)
	done

	for ((i = 0; i < 8; i++)); do
		items+=( \
			"MZ${SLOT_NUM}_TTL$[i+9]" \
			$[GPIO_BASE+i] \
			"input" \
			"active-high" \
		)
	done

	wb_gpio_add "${items[@]}"
}

hook_module_del() {
	systemctl stop wb-mqtt-gpio || true
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+GPIO_COUNT-1])
}

hook_module_deinit() {
	for ((i = 0; i < GPIO_COUNT; i++)); do
		echo $[GPIO_BASE+i] > /sys/class/gpio/unexport 2>/dev/null || true
	done
}

hook_once_after_config_change "restart_service wb-homa-gpio"
