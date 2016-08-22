#define SLOT_INT		(AUART2_CTS,	3,	10)

#define SLOT_I2C_ALIAS	&i2c0

#include "imx28-pinfunc.h"
#include "irq.h"
#include "utils.h"

#ifdef FROM_SHELL
local GPIO_BASE_8=SLOT_GPIO_BASE_8
local GPIO_BASE_40=SLOT_GPIO_BASE_40
#endif
