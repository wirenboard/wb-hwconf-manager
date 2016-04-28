source "$DATADIR/modules/utils.sh"

local CONFIG_ADC=${CONFIG_ADC:-/etc/wb-homa-adc.conf}
local I2C_ADDR=48

hook_module_add() {
	local JSON=$CONFIG_ADC
	local items=()
	local chan mul max_voltage
	for chan in 0 1; do
		local gain="$(config_module_option ".channels[$chan].gain // 1")"
		case "$(config_module_option ".channels[$chan].mode // \"voltage\"")" in
			voltage)
				mul=1
				;;
			voltage_x10)
				mul=10
				;;
			current)
				mul=0.02004
				;;
		esac
		items+=( "{
			id: \"MOD${SLOT_NUM}_A$((chan+1))\",
			averaging_window: 1,
			match_iio: \"mod${SLOT_NUM}_i2c\",
			channel_number: $chan,
			voltage_multiplier: (${mul}*${gain}),
			decimal_places: 3,
			max_voltage: 3.3
		}" )
		shift 3
	done
	json_array_append ".iio_channels" "${items[@]}"

	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc /devices/wb-adc/#"
}

hook_module_del() {
	local JSON=$CONFIG_ADC
	json_array_delete ".iio_channels" \
		". as \$chan | ([\"MOD${SLOT_NUM}_A1\", \"MOD${SLOT_NUM}_A2\"] | map(. == \$chan.id) | any)"
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc /devices/wb-adc/#"
}

hook_module_init() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo "ads1015 0x${I2C_ADDR}" > $bus/new_device

	local dev=$(slot_i2c_dev_sysfs $I2C_ADDR)
	wait_for_path "$dev"

	local chan
	for chan in 0 1; do
		config_module_option ".channels[$chan].gain // 1" > $(echo "$dev/iio:device"*"/in_voltage${chan}_scale")
	done
}

hook_module_deinit() {
	local bus=$(slot_i2c_bus_sysfs)
	[[ -d "$bus" ]] || {
		log "Unable to find i2c bus for slot $SLOT (sysfs: $bus)"
		return 1
	}
	echo "0x${I2C_ADDR}" > $bus/delete_device
}
