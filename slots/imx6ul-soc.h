#ifndef __DTS_IMX6UL_PINFUNC_H
#define __DTS_IMX6UL_PINFUNC_H

#define SOC_TYPE MX6UL

// GPIO ports in DT counts from 1, and in sysfs GPIO interface from 0
#define GPIO_PORT_PIN_TO_NUM(port, pin) $(((port-1) * 32 + pin))

#include "imx-common.h"
#include "imx6ul-pinfunc.h"
#endif
