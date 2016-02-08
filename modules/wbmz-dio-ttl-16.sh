source "$DATADIR/modules/utils.sh"

local GPIO_BASE=224
local GPIO_COUNT=16

hook_module_add() {
	local items=()
	for ((i = 0; i < GPIO_COUNT; i++)); do
		items+=( \
			"MZ${SLOT_NUM}_TTL$[i+1]" \
			$[GPIO_BASE+i] \
			"input" \
		)
	done
	wb_gpio_add "${items[@]}"
}

hook_module_del() {
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+GPIO_COUNT-1])
}

hook_once_after_config_change "restart_service wb-homa-gpio"
