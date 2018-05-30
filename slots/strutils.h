#ifndef STRUTILS_H
#define STRUTILS_H

/* For somewhat reason, tcc assumes that linux equals 1 */
#undef linux

/* Abusing the preprocessor violently */
#define __cat_internal(a, ...) a ## __VA_ARGS__
#define __cat(a, ...) __cat_internal(a, __VA_ARGS__)
#define __cat3(a, b, ...) __cat(a, __cat(b, __VA_ARGS__))
#define __cat4(a, b, c, ...) __cat(a, __cat3(b, c, __VA_ARGS__))
#define __pass(...) __VA_ARGS__

/* Append '0x' prefix to hex numbers */
#define HEX_PREFIX(x) __cat(0x, x)

#define __arg1(a, ...) a
#define __arg2(a, b, ...) b
#define __arg3(a, b, c, ...) c
#define __arg4(a, b, c, d, ...) d
#define __arg5(a, b, c, d, e, ...) e

#define QUOTE(str) #str
#define EXPAND_AND_QUOTE(str) QUOTE(str)

#endif /* STRUTILS_H */
