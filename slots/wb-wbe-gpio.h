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
