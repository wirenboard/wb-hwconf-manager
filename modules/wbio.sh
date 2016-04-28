source "$DATADIR/modules/utils.sh"

case "$MODULE" in
	*-di-*)
		GPIO_DIR=input
		;;
	*-do-*|*-dio-*)
		GPIO_DIR=output
		;;
esac

hook_module_add() {
	# Add WBIO_COUNT gpios with names and directions specified
	# in WBIO_NAME and WBIO_DIR arrays
	local items=()
	for ((i = 0; i < WBIO_COUNT; i++)); do
		items+=( \
			"EXT${SLOT_NUM}_${WBIO_GPIO_PREFIX}$[i+1]" \
			$[GPIO_BASE+i] \
			"$GPIO_DIR" \
		)
	done
	wb_gpio_add "${items[@]}"
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	# Remove all the added gpios
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
