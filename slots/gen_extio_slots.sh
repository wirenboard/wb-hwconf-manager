#!/bin/bash
addr=(0 1 2 4)

for board_inc in *-extio.h; do
	board_type=${board_inc%%-extio.h}
	echo "Generating extio slots for ${board_type}"

	for i in {0..7}; do
		slot=$[i+1]
		cat > "${board_type}-extio${slot}.def" <<EOF
#define EXTIO_SLOT_NUM ${slot}

#include "wb-extio-v1.h"
#include "${board_inc}"
EOF
	done
done
