
/* order for EXTIO_INPUT and EXTIO_OUTPUT_HIGH
   must be two digit number, 1 must be 01, 2 - 02 etc.
   The macros concatenates EXTIO_SLOT_NUM and supplied order.
   Resulting sort order for extio pins starts from 100.
*/
#define WBE_INPUT(name, pin, order) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        input;\
        sort-order = <__cat(MOD_SLOT_NUM, order)>;\
    }

#define WBE_OUTPUT_HIGH(name, pin, order) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        output-high;\
        sort-order = <__cat(MOD_SLOT_NUM, order)>;\
    }
