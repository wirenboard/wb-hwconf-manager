#define SLOT_INT		(8, 18)

#define SLOT_I2C_ALIAS	&i2c1

#include "r40-soc.h"


#include "strutils.h"

#define SLOT_ALIAS __cat(extio, EXTIO_SLOT_NUM)

/* utils.h has to be included after SLOT_ALIAS is defined */
#include "utils.h"

/* Fields: ADDRESS_IN (hex), ADDRESS_OUT (hex), ADDRESS_DAC (hex), GPIO_BASE_8, GPIO_BASE_40 */
#define SLOT1 ( 27,	20, 31, 512, 512 )
#define SLOT2 ( 26,	21, 33,	552, 552 )
#define SLOT3 ( 25,	22, 43, 592, 592 )
#define SLOT4 ( 23,	24, 52, 632, 632 )
#define SLOT5 ( 27,	20, 31, 672, 672 )
#define SLOT6 ( 26,	21, 33, 712, 712 )
#define SLOT7 ( 25,	22, 43, 752, 752 )
#define SLOT8 ( 23,	24, 52, 792, 792 )


#include "wb-extio-common.h"

#ifdef FROM_SHELL
local SLOT_I2C_DEVICE_MATCH="1c2b000.i2c"
#endif
