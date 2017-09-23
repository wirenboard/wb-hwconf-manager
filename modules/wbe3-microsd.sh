source "$DATADIR/modules/utils.sh"

hook_module_init() {
	modprobe mmc-spi
}
