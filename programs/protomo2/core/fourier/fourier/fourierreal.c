/*----------------------------------------------------------------------------*
*
*  fourierreal.c  -  fourier: Fourier transforms
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

extern Status FourierReal
              (Size dim,
               const Size *len,
               const Real *src,
               Cmplx *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierRealEven
              (Size dim,
               const Size *len,
               const Real *src,
               Real *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq | FourierEven | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}


extern Status FourierRealOdd
              (Size dim,
               const Size *len,
               const Real *src,
               Imag *dst,
               Size count,
               FourierOpt opt)

{
  Fourier *fou;
  Status status, stat;

  fou = FourierInit( dim, len, opt, FourierForward | FourierRealSeq | FourierOdd | FourierMulti );
  status = testcondition( fou == NULL );
  if ( popexception( status ) ) return status;

  status = FourierTransf( fou, src, dst, count );
  logexception( status );

  stat = FourierFinal( fou );
  logexception( stat );
  if ( !status ) status = stat;

  return status;

}
