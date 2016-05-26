source "$DATADIR/modules/utils.sh"

hook_module_init() {
	hwclock -s
}