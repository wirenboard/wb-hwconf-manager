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
}

hook_module_del() {
	# Remove all the added gpios
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])
}

# Delete empty slots at the end of chain so that only one is left
wbio_update_slots() {
	local SLOT_TYPE=${SLOT_TYPE:-$1}
	local last_slot=$(wb_max_slot_num "$SLOT_TYPE")
	local last_used_slot=$(
		config_parse |
		sed -r "/^${SLOT_TYPE}.+ \\S+$/h; \$!d; x; s/${SLOT_TYPE}([0-9]+).*/\\1/"
	)

	if [[ "$last_slot" -le "$last_used_slot" &&
		  "$last_slot" -lt 8 ]]; then
		config_slot_add \
			"${SLOT_TYPE}$[last_slot+1]" \
			"${SLOT_TYPE}" \
			"External I/O module $[last_slot+1]"
	elif [[ "$[last_used_slot+2]" -le "$last_slot" ]]; then
		log "Cleaning up unused $SLOT_TYPE slots"
		local i
		for ((i = last_used_slot+2; i <= last_slot; i++)); do
			config_slot_del "${SLOT_TYPE}${i}"
		done
	fi
}
hook_once_after_config_change "wbio_update_slots $SLOT_TYPE"

hook_once_after_config_change "service wb-homa-gpio restart"
