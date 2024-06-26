/*----------------------------------------------------------------------------*
*
*  fourierinvcmplxinit.c  -  fourier: Fourier transforms
*
*-----------------------------------------------------------------------------*
*
*  Copyright � 2012 Hanspeter Winkler
*
*  This software is distributed under the terms of the GNU General Public
*  License version 3 as published by the Free Software Foundation.
*
*----------------------------------------------------------------------------*/

#include "fouriercommon.h"
#include "exception.h"


/* functions */

extern Fourier *FourierInvCmplxInit
                (Size dim,
                 const Size *len,
                 FourierOpt opt)

{
  Fourier *fou;

  fou = FourierInit( dim, len, opt, FourierBackward );
  testcondition( fou == NULL );

  return fou;

}
