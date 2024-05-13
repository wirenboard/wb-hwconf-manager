#ifndef __DTS_T507_PINFUNC_H
#define __DTS_T507_PINFUNC_H

#define SOC_TYPE T507

#include "allwinner-soc.h"

#endif

// ao-10v-2 driver needs vdd-regulator phandle
#ifndef SLOT_VDD_SUPPLY
#define SLOT_VDD_SUPPLY &reg_periph_on
#endif
