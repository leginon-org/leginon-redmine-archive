/*----------------------------------------------------------------------------*
*
*  swap16.c  -  core: swap bytes
*
*-----------------------------------------------------------------------------*
*
*  Copyright � 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "baselib.h"


/* functions */

extern void Swap64
            (Size size,
             const void *src,
             void *dst)

{
  const uint8_t *s = src;
  uint8_t *d = dst;

  while ( size-- ) {
    uint8_t v0 = *s++;
    uint8_t v1 = *s++;
    uint8_t v2 = *s++;
    uint8_t v3 = *s++;
    uint8_t v4 = *s++;
    uint8_t v5 = *s++;
    uint8_t v6 = *s++;
    uint8_t v7 = *s++;
    *d++ = v7;
    *d++ = v6;
    *d++ = v5;
    *d++ = v4;
    *d++ = v3;
    *d++ = v2;
    *d++ = v1;
    *d++ = v0;
  }

}
