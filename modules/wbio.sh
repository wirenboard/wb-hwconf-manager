case "$MODULE" in
	*-di-*)
		GPIO_DIR=input
		;;
	*-do-*|*-dio-*)
		GPIO_DIR=output
		;;
esac

if [ -z ${WBIO_CHANNEL_GPIO_OFFSETS+x} ]; then
	local WBIO_CHANNEL_GPIO_OFFSETS=()
	for ((i = 0; i < WBIO_COUNT; i++)); do
		WBIO_CHANNEL_GPIO_OFFSETS[i]=i;
	done
fi

hook_module_add() {
	# Add WBIO_COUNT gpios with names and directions specified
	# in WBIO_NAME and WBIO_DIR arrays
	local items=()
	for ((i = 0; i < WBIO_COUNT; i++)); do
		items+=( \
			"EXT${SLOT_NUM}_${WBIO_GPIO_PREFIX}$[i+1]" \
			$[GPIO_BASE+WBIO_CHANNEL_GPIO_OFFSETS[i]] \
			"$GPIO_DIR" \
			"active-high" \
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
