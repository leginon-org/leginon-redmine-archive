/*----------------------------------------------------------------------------*
*
*  polar_3d_uint8_real.c  -  array: spatial polar transformations
*
*-----------------------------------------------------------------------------*
*
*  Copyright � 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "polar.h"
#include "exception.h"
#include "mathdefs.h"


/* functions */

extern Status Polar3dUint8Real
              (const Size *srclen,
               const void *srcaddr,
               const Coord *A,
               const Coord *b,
               const Size *dstlen,
               void *dstaddr,
               const Coord *c,
               const TransformParam *param)

#define SRCTYPE uint8_t
#define DSTTYPE Real

#define DSTTYPEMIN (-RealMax)
#define DSTTYPEMAX (+RealMax)

#include "polar_3d.h"
