source "$DATADIR/modules/utils.sh"

AXP20X_BAT_PS_NAME="axp20x-battery-power-supply"
AXP20X_BAT_PS_DRIVER_DIR="/sys/bus/platform/drivers/${AXP20X_BAT_PS_NAME}"

axp20x_bat_ps_bind() {
	if [[ -e "${AXP20X_BAT_PS_DRIVER_DIR}/bind" ]]; then
		echo "${AXP20X_BAT_PS_NAME}" > "${AXP20X_BAT_PS_DRIVER_DIR}/bind" || true
	fi
}

axp20x_bat_ps_unbind() {
	if [[ -e "${AXP20X_BAT_PS_DRIVER_DIR}/${AXP20X_BAT_PS_NAME}" ]]; then
		echo "${AXP20X_BAT_PS_NAME}" > "${AXP20X_BAT_PS_DRIVER_DIR}/unbind" || true
	fi
}
