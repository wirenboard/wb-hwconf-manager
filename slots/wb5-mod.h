/* Definitions common for all WB5 internal extension slots */

/* All known pins for module */
#define MOD_ALL_PINS \
	MOD_FOR_PIN(RX) \
	MOD_FOR_PIN(TX) \
	MOD_FOR_PIN(RTS) \
	MOD_FOR_PIN(SDA) \
	MOD_FOR_PIN(SCL) \
	MOD_FOR_PIN(MOSI) \
	MOD_FOR_PIN(MISO) \
	MOD_FOR_PIN(SCK) \
	MOD_FOR_PIN(CS)

#include "imx28-pinfunc.h"
#include "utils.h"
