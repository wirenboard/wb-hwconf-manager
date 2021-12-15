WBIO_COUNT=8
WBIO_CHANNEL_COUNT=4

source "$DATADIR/modules/utils.sh"
GPIO_BASE=${GPIO_BASE_8}

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
    for ((i = 0; i < WBIO_CHANNEL_COUNT; i++)); do
        items+=( \
            "EXT${SLOT_NUM}_DIR$[i+1]" \
            $[GPIO_BASE+i*2] \
            "$GPIO_DIR" \
            "active-high" \
        )

        items+=( \
            "EXT${SLOT_NUM}_ON$[i+1]" \
            $[GPIO_BASE+i*2+1] \
            "$GPIO_DIR" \
            "active-high" \
        )


    done
    wb_gpio_add "${items[@]}"
    hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
    systemctl stop wb-mqtt-gpio || true
    # Remove all the added gpios
    wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])
    hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_deinit() {
    for ((i = 0; i < WBIO_COUNT; i++)); do
        echo $[GPIO_BASE+i] > /sys/class/gpio/unexport 2>/dev/null || true
    done
}