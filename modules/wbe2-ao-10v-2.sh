source "$DATADIR/modules/utils.sh"
local CONFIG_DAC=${CONFIG_DAC:-/etc/wb-mqtt-dac.conf}
local IIO_OF_NAME="${SLOT_ALIAS}_wbe2_ao_10v_2"

hook_module_add() {
    local JSON=$CONFIG_DAC
    local items=()
    local chan
    for chan in 0 1; do
        items+=( "{
            id: \"MOD${SLOT_NUM}_O$((chan+1))\",
            iio_channel: $chan,
            iio_of_name: \"${IIO_OF_NAME}\",
            max_value_mv: 10000,
            multiplier: 3.75
        }" )
        shift 3
    done
    json_array_append ".channels" "${items[@]}"

    hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wb-dac/#"
}


hook_module_del() {
    local JSON=$CONFIG_DAC
    json_array_delete ".channels" ".iio_of_name==\"${IIO_OF_NAME}\""
    hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wb-dac/#"
}
