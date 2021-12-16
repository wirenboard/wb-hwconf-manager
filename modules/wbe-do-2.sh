source "$DATADIR/modules/utils.sh"

hook_module_add() {
    wb_gpio_add "MOD${SLOT_NUM}_K1" ${!DO2_GPIO_K1} output active-high
    wb_gpio_add "MOD${SLOT_NUM}_K2" ${!DO2_GPIO_K2} output active-high
    hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
    systemctl stop wb-mqtt-gpio || true
    wb_gpio_del ${!DO2_GPIO_K1}
    wb_gpio_del ${!DO2_GPIO_K2}
    hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_deinit() {
    echo ${!DO2_GPIO_K1} > /sys/class/gpio/unexport 2>/dev/null || true
    echo ${!DO2_GPIO_K2} > /sys/class/gpio/unexport 2>/dev/null || true
}