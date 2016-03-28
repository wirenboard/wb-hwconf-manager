source "$DATADIR/modules/utils.sh"

hook_module_init() {
    echo $GPIO_RX > /sys/class/gpio/export
    echo low > /sys/class/gpio/gpio${GPIO_RX}/direction

    local BUS_NUM=`grep -l '^${SLOT_ALIAS}@0$' /sys/bus/i2c/devices/i2c-*/name  | grep -Po '(?<=i2c-)(\d+)'`

    local JSON="/etc/wb-mqtt-am2320.conf"
    json_edit ".i2c_bus = ${BUS_NUM}"

    service wb-mqtt-am2320 restart
}

hook_module_deinit() {
    echo ${GPIO_RX} > /sys/class/gpio/unexport
}

