source "$DATADIR/modules/utils.sh"

local CONFIG_ADC=${CONFIG_ADC:-/etc/wb-homa-adc.conf}
local I2C_ADDR=48

hook_module_add() {
	local JSON=$CONFIG_ADC
	local items=()
	local chan mul
	for chan in 0 1; do
		case "$(config_module_option ".channels[$chan].mode")" in
			voltage)
				mul=1.0
				;;
			voltage_x10)
				mul=10
				;;
			current)
				mul=0.02
				;;
		esac
		items+=( "{
			id: \"MOD${SLOT_NUM}_A$((chan+1))\",
			averaging_window: 1,
			match_iio: \"mod${SLOT_NUM}_i2c\",
			channel_number: $chan,
			multiplier: $mul,
			decimal_places: 3,
			max_voltage: 7
		}" )
		shift 3
	done
	json_array_append ".iio_channels" "${items[@]}"

	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}

hook_module_del() {
	local JSON=$CONFIG_ADC
	json_array_delete ".iio_channels" \
		". as \$chan | ([\"MOD${SLOT_NUM}_A1\", \"MOD${SLOT_NUM}_A2\"] | map(. == \$chan.id) | any)"
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}

hook_module_init() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo "ads1015 0x${I2C_ADDR}" > $bus/new_device
}

hook_module_deinit() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo "0x${I2C_ADDR}" > $bus/delete_device
}
