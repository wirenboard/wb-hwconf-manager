source "$DATADIR/modules/utils.sh"

hook_module_add() {
    hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}

hook_module_del() {
    systemctl stop wb-mqtt-gpio || true
    wb_gpio_del ${!DO2_GPIO_K1}
    wb_gpio_del ${!DO2_GPIO_K2}
    hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}
