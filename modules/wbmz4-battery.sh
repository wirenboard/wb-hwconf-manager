source "$DATADIR/modules/utils.sh"
source "$DATADIR/modules/axp20x-utils.sh"

hook_module_init() {
	axp20x_bat_ps_unbind
	axp20x_bat_ps_bind
}

hook_module_deinit() {
	axp20x_bat_ps_unbind
	axp20x_bat_ps_bind
}
