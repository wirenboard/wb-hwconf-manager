source "$DATADIR/modules/utils.sh"

hook_module_add() {
	# Add WBIO_COUNT gpios with names and directions specified
	# in WBIO_NAME and WBIO_DIR arrays
	local items=()
	for ((i = 0; i < WBIO_COUNT; i++)); do
		items+=( \
			"EXT${SLOT_NUM}_${WBIO_NAME[i]}" \
			$[GPIO_BASE+i] \
			"${WBIO_DIR[i]}" \
		)
	done
	wb_gpio_add "${items[@]}"

	# If we are just used last available slot, add extra one for daisy-chaining
	[[ `wb_max_slot_num "$SLOT_TYPE"` == "$SLOT_NUM" ]] &&
		config_slot_add \
			"${SLOT_TYPE}$[SLOT_NUM+1]" \
			"${SLOT_TYPE}" \
			"External I/O module $[SLOT_NUM+1]"

	[[ -z "$NO_RESTART_SERVICE" ]] && service wb-homa-gpio restart
}

hook_module_del() {
	# Remove all the added gpios
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])

	[[ `wb_max_slot_num "$SLOT_TYPE"` -le $[SLOT_NUM+1] &&
		-z `config_slot_module "${SLOT_TYPE}$[SLOT_NUM+1]"` ]] &&
		config_slot_del "${SLOT_TYPE}$[SLOT_NUM+1]"

	[[ -z "$NO_RESTART_SERVICE" ]] && service wb-homa-gpio restart
}
