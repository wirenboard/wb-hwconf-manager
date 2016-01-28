/* Definitions common for all WB5 internal extension slots */

/* All known pins for module */
#define SLOT_ALL_PINS \
	SLOT_FOR_PIN(RX) \
	SLOT_FOR_PIN(TX) \
	SLOT_FOR_PIN(RTS) \
	SLOT_FOR_PIN(SDA) \
	SLOT_FOR_PIN(SCL) \
	SLOT_FOR_PIN(MOSI) \
	SLOT_FOR_PIN(MISO) \
	SLOT_FOR_PIN(SCK) \
	SLOT_FOR_PIN(CS)

#include "imx28-pinfunc.h"
#include "utils.h"
