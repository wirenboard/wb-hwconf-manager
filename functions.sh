#!/bin/bash
CONFIG="/etc/wb-hardware.conf"
DATADIR="${DATADIR:-/usr/share/wb-hwconf-manager}"
MODULES="$DATADIR/modules"
SLOTS="$DATADIR/slots"

CONFIGFS="/sys/kernel/config"
OVERLAYS="$CONFIGFS/device-tree/overlays"

VERBOSE="yes"
. /lib/lsb/init-functions 2>/dev/null

die() {
	#>&2 echo "[${FUNCNAME[1]}] ERROR: $@"
	log_failure_msg "$@"
	#[[ $? == 0 ]] && exit 1 || exit $?
}

overlay_path() {
	echo "$OVERLAYS/$1:$2"
}

dtbo_check_compatible() {
	local dtbo_compat=`fdtget "$1" / compatible 2>/dev/null`
	[[ -z "$dtbo_compat" || "$dtbo_compat" == "unknown" ]] && return 0
	for compat in `r < /proc/device-tree/compatible  '\000' '\n'`; do
		[[ "$dtbo_compat" == "$compat" ]] && return 0
	done
	return 1
}

dtbo_build() {
	local _slot=$1
	local _mod=$2
	[[ -z "$_slot" || -z "$_mod" ]] && {
		die "Bad arguments"
		return 1
	}

	local slot="$SLOTS/${_slot}.def"
	[[ -f "$slot" ]] || {
		die "Slot definition file ${slot} not found"
		return 1
	}

	local mod="$MODULES/${_mod}.dtso"
	[[ -f "$mod" ]] || {
		die "Module definition file ${mod} not found"
		return 1
	}

	{
		echo '/dts-v1/ /plugin/;'
		cat "$slot" "$mod"
	} | tcc \
		-x assembler-with-cpp \
		-nostdinc \
		-I "$SLOTS" -I "$MODULES" -E - |
	dtc -I dts -O dtb -@ -
}

module_bind() {
	local _slot=$1
	local _mod=$2

	local t=`echo "$OVERLAYS/$_slot:"*`
	[[ -d "$t" ]] && {
		local st="$(cat "$t/status")"
		case "$st" in
			"applied")
				die "Slot $_slot is used by ${t#$OVERLAYS/$_slot:} module"
				return 1
				;;
			*)
				log_warning_msg "Overlay ${t#$OVERLAYS/} have status '$st', try to remove"
				rmdir "$t"
				;;
		esac
	}
	t=`echo "$OVERLAYS/$_slot:"*`
	[[ -d "$t" ]] && {
		die "Overlays conflict on slot $_slot"
		return 1
	}

	log_action_msg "Binding module $_mod to slot $_slot"

	local dtbo=`mktemp`
	dtbo_build $_slot $_mod > "$dtbo"
	dtbo_check_compatible "$dtbo" || {
		rm "$dtbo"
		die "Device Tree overlay is incompatible with this device"
		return 1
	}

	local overlay=`overlay_path $_slot $_mod`
	mkdir "$overlay" &&
	cat "$dtbo" > "$overlay/dtbo"

	local i
	for ((i=0; i<5; i++)); do
		log_action_cont_msg
		[[ $(cat "$overlay/status") == "applied" ]] && break
		sleep 1
	done
	[[ $i == 3 ]] && {
		rm "$dtbo"
		die "Device Tree overlay loading failed"
		return 1
	}

	rm "$dtbo"
}

module_unbind() {
	local _slot=$1

	log_action_msg "Unbinding module from slot $_slot"
	local t=`echo "$OVERLAYS/$_slot:"*`
	[[ -e "$t" ]] || {
		log_end_msg "Slot $_slot is not in use"
	}

	rmdir "$t"
}

config_parse() {
	jq -r '.slots[] | @text "\(.id) \(.module)"' "$CONFIG"
}
