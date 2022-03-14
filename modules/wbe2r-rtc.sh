source "$DATADIR/modules/utils.sh"

# rtc-rv8803 driver rejects all date-time communications with device, if bit RV8803_FLAG_V2F (power loss) is set
# calling rv8803_set_time clears power-loss flag & enables datetime communications

# => calling hwclock -w to initiallize RTC, if systime is appropriate (synchronized with NTP)
hook_module_init() {
	modprobe rtc-rv8803

	if hwclock --show ; then
		return 0
	else
		log "RTC chip was powered OFF. Performing first initiallization.."
	fi

	if ntpstat ; then
		if hwclock -w ; then
			log "Proper systime has written into RTC"
		else
			log "No connection to RTC device"
			return 1
		fi
	else
		log "RTC needs proper systime to initiallization, but systime is not synchronized with NTP"
		return 1
	fi
}
