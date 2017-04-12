source "$DATADIR/modules/utils.sh"

set_hwclock_rtc_dev() {
    # this may cause problems if there were commented-out HCTOSYS_DEVICE lines
    sed -i.bak 's/^#*HCTOSYS_DEVICE=rtc./HCTOSYS_DEVICE=rtc'$1/ /etc/default/hwclock
}

hook_module_init() {

    # set time from RTC if only it looks reasanoble (e.g. > 2013-01-01)
    HW_RTC_EPOCH=`cat /sys/class/rtc/rtc1/since_epoch`
    local RC=$?
    if [[ $RC == 0 ]]; then
        if (( ${HW_RTC_EPOCH} > 1356998400 )); then
    	   hwclock -f /dev/rtc1 -s
        fi;
    else
        # error reading time from RTC, initialize it with system time
        hwclock -f /dev/rtc1 -w
    fi

    set_hwclock_rtc_dev 1
}

hook_module_deinit() {
    set_hwclock_rtc_dev 0
}