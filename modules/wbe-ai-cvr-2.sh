source "$DATADIR/modules/utils.sh"

hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}

hook_module_del() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}

hook_module_init() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo 'ads1015 0x48' > $bus/new_device
}

hook_module_deinit() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo '0x48' > $bus/delete_device
}
