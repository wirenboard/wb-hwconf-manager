source "$DATADIR/modules/utils.sh"

# rtc-rv8803 driver rejects all date-time communications with device, if bit RV8803_FLAG_V2F (power loss) is set
# calling rv8803_set_time clears power-loss flag & enables datetime communications

# => calling hwclock -w to initiallize RTC, if systime is appropriate (synchronized with NTP)
hook_module_init() {
	hwclock --show && return 0 || {
		log "RTC chip was powered OFF. Performing first initiallization.."
		ntpstat && {
			hwclock -w && log "Proper systime has written into RTC" || {
				log "No connection to RTC device"
				return 1
				}
			} || {
			log "RTC needs proper systime to initiallization, but systime is not synchronized with NTP"
			return 1
		}
	}
}
