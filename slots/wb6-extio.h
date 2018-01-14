#define SLOT_INT		(SD1_DATA0,	2,	18)

#define SLOT_I2C_ALIAS	&i2c2

#include "imx6ul-pinfunc.h"
#include "wb-extio-v1.h"

#ifdef FROM_SHELL
local SLOT_I2C_DEVICE_MATCH="21a4000.i2c"
#endif
