#define MOD_INT		(AUART2_CTS,	3,	10)

#define MOD_I2C_ALIAS	extio_i2c

#include "imx28-pinfunc.h"
#include "irq.h"
#include "utils.h"

#ifdef FROM_SHELL
local GPIO_BASE=MOD_GPIO_BASE
#endif
