source "$DATADIR/modules/utils.sh"
local CONFIG_DAC=${CONFIG_DAC:-/etc/wb-mqtt-dac.conf}
local IIO_OF_NAME="${SLOT_ALIAS}_ao10v8"

hook_module_add() {
    local JSON=$CONFIG_DAC
    local OUT_TO_CHIP_CHAN_MAP=(3 2 1 0 7 6 5 4)
    local items=()
    local chan
    for chan in 1 2 3 4 5 6 7 8; do
        local iio_chan=${OUT_TO_CHIP_CHAN_MAP[chan-1]}
        items+=( "{
            id: \"EXT${EXTIO_SLOT_NUM}_O$chan\",
            iio_channel: $iio_chan,
            iio_of_name: \"${IIO_OF_NAME}\",
            max_value_mv: 10000,
            multiplier: 9.77518
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
