/* Common definitions of battery slot for wb6.x boards */
#define SLOT_PIN1_SCL		(UART1_CTS_B,	1,	18)
#define SLOT_PIN2_SDA		(UART1_RTS_B,	1,	19)

/* All known pins for module */
#define SLOT_ALL_PINS \
	SLOT_FOR_PIN(PIN1_SCL) \
	SLOT_FOR_PIN(PIN2_SDA)

#include "imx6ul-soc.h"  // should be included after SLOT_ALL_PINS is defined

#include "utils.h"
