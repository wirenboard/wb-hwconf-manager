#!/bin/bash

basedir=$(readlink -f "$PWD/..")
tmpdir="${basedir}/test/tmp"
. ${tmpdir}/functions.sh

########################################################
# Minimalistic test framework :]
########################################################

c_normal="\033[0m"
c_ok="\033[1;32m"
c_err="\033[1;31m"

tests_failed=()

test_run() {
	echo -n "* $@: "
	if "$@"; then
		echo -e "${c_ok}OK${c_normal}"
	else
		echo -e "${c_err}FAIL${c_normal}"
		tests_failed+=("$*")
	fi
}

test_summary() {
	echo
	[[ "${#tests_failed[@]}" == 0 ]] && {
		echo "All tests passed"
		return 0
	}
	echo "Failed tests:"
	for t in "${tests_failed[@]}"; do
		echo "$t"
	done
	return "${#tests_failed[@]}"
}

########################################################
# Some helper funcs 
########################################################

for_each_slot() {
	local slot
	for slot in $SLOTS/*.def; do
		slot="$(basename "$slot")"
		"$@" "${slot%%.def}"
	done
}

for_each_file() {
	local f
	local glob="$1"
	shift
	for f in $glob; do
		"$@" "$f"
	done
}

config_slot_compatible() {
	local SLOT="$1"
	jq -r -e ".slots[] | select(.id == \"$SLOT\") | .compatible[]" "$JSON"
}

get_slot_module_pairs() {
	local JSON="$1"
	local slot comp mod
	for slot in $(jq -r ".slots[] | .id" "$JSON"); do
		config_slot_compatible "$slot" | while read comp; do
			grep -rlw "$comp" "$MODULES" | while read mod; do
				mod=$(basename "$mod")
				echo "$slot" "${mod%%.dtso}"
			done
		done
	done
}


########################################################
# The test cases
########################################################

# Test if all slot pins have valid GPIO pinmux.
# This also ensures there are no spelling errors in pad names
test_slot_gpio() {
	local SLOT="$1"
	{
		slot_preprocess <<EOF
#ifdef SLOT_ALL_PINS
#define SLOT_FOR_PIN(pin) SLOT_PINMUX_GPIO(pin)
SLOT_ALL_PINS
#else
0xff
#endif
EOF
	} | sed 's/ /\n/g' | grep -Ev '^(0x[0-9a-f]+|[0-9]+)$' >/dev/null && return 1
	return 0
}

test_dtbo_build() {
	local SLOT="$1"
	local MODULE="$2"
	dtbo_build >/dev/null
}


for_each_slot test_run test_slot_gpio
pairs=$( for_each_file "$DATADIR/wb-hardware.conf.wb*" get_slot_module_pairs | sort -u )
while read SLOT MODULE; do
	test_run test_dtbo_build "$SLOT" "$MODULE"
done <<<"$pairs"

test_summary
