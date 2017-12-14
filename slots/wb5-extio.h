#define SLOT_INT		(AUART2_CTS,	3,	10)

#define SLOT_I2C_ALIAS	&i2c0

#include "imx28-pinfunc.h"
#include "wb-extio-v1.h"

#ifdef FROM_SHELL
local SLOT_I2C_DEVICE_ALIAS="i2c-0"
#endif
