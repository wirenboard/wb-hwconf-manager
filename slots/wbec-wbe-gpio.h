#undef WBE_INPUT
#define WBE_INPUT(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        input;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }

#undef WBE_OUTPUT_HIGH
#define WBE_OUTPUT_HIGH(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }
