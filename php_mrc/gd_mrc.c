#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "php.h"
#include "gd.h"
#include "mrc.h"
#include "gd_mrc.h"
#include "filter.h"

/* {{{ void mrc_to_float(MRC *mrc, float *pdata_array) */
void mrc_to_float(MRC *mrc, float *pdata_array) {
        float   fmin=mrc->header.amin,
                fmax=mrc->header.amax;

        int     h=mrc->header.nx, w=mrc->header.ny,
                mode=mrc->header.mode,
                n=w*h,
                i;

        switch (mode) {
         case MRC_MODE_BYTE:
         {
                char *data_array_char = (char *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_char[i];
                }

         }
         break;
         case MRC_MODE_SHORT:
         {
                short *data_array_short = (short *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_short[i];
                }


         }
         break;
         case MRC_MODE_FLOAT:
         {
                memcpy(pdata_array, (float *)mrc->pbyData, sizeof(float)*n);

         }
         break;
         case MRC_MODE_UNSIGNED_SHORT:
         {
                unsigned short *data_array_ushort = (unsigned short *)mrc->pbyData;
                for (i = 0; i < n; ++i) {
                        pdata_array[i] = (float)data_array_ushort[i];
                }
         }
         break;
        }
}
/* }}} */

/* {{{ void mrc_copy(MRC *mrc_src, MRC *mrc_dst, int x1, int y1, int x2, int y2) */
void mrc_copy(MRC *mrc_src, MRC *mrc_dst, int x1, int y1, int x2, int y2) {

        float	*data_array, *data_array_dst;

        int     w_src=mrc_src->header.nx, h_src=mrc_src->header.ny,
                n_src=w_src*h_src,
		w_dst, h_dst, n_dst,
		x_min=x1, x_max=x2,
		y_min=y1, y_max=y2,
                i,j,ij,t;

	if (x1>x2) {
		x_min=x2;
		x_max=x1;
	}
	if (y1>y2) {
		y_min=y2;
		y_max=y1;
	}
	if (x_max > w_src)
		x_max = w_src;
	if (y_max > h_src)
		y_max = h_src;

	w_dst = x_max-x_min;
	h_dst = y_max-y_min;
	n_dst=w_dst*h_dst;

	memcpy(&mrc_dst->header, &mrc_src->header, MRC_HEADER_SIZE);

	mrc_dst->header.nx = w_dst;
	mrc_dst->header.ny = h_dst;
	mrc_dst->header.mode = MRC_MODE_FLOAT;

        mrc_dst->pbyData = malloc(sizeof(float)*n_dst);
	data_array_dst = (float *)mrc_dst->pbyData;
	
	data_array = malloc(sizeof(float)*n_src);
	mrc_to_float(mrc_src, data_array);

	for (t=0, j=y_min; j<y_max; j++) {
		for (i=x_min; i<x_max; i++) {
			ij = i + j*w_src;
			data_array_dst[t] = data_array[ij];
			t++;
		}
	}
	free(data_array);
}
/* }}} */

/* {{{ MRCPtr mrc_create(int x_size, int y_size) */
MRCPtr mrc_create(int x_size, int y_size) {

	int n = x_size * y_size;

	MRCPtr pmrc;
	pmrc = (MRC *) malloc (sizeof (MRC));
	memset (pmrc, 0, sizeof (MRC));
	pmrc->header.nx = x_size;
	pmrc->header.ny = y_size;
	pmrc->header.nz = 1;
	pmrc->header.mode = MRC_MODE_FLOAT;
	pmrc->pbyData = malloc(sizeof(float)*n);
	memset (pmrc->pbyData, 0, sizeof(float)*n);

	return pmrc;
}
/* }}} */


/* {{{ void mrc_update_header(MRC *mrc) */
void mrc_update_header(MRC *mrc) {

	int	i=0;
	double	somme=0, somme2=0, n=0; 

        float   fmin,
                fmax,
                fmean,
                stddev,
                f_val;

	float *data_array;

	data_array = (float *)mrc->pbyData;
	n = mrc->header.nx * mrc->header.ny;

	fmax = fmin = data_array[0];
	for (i = 0; i < n; i++) {
		f_val = data_array[i];
		fmax = MAX(fmax, f_val);
		fmin = MIN(fmin, f_val);
		somme  += f_val;
		somme2 += f_val*f_val;
	}

	if (n>0) {
		fmean = somme/n;
		stddev = sqrt((somme2 * n - somme * somme) / (n*n));
	}

	mrc->header.amin = fmin;
	mrc->header.amax = fmax;
	mrc->header.amean = fmean;
	mrc->header.rms = stddev;

}
/* }}} */

/* {{{ void mrc_filter(MRC *mrc, int binning, int kernel, float sigma) */
void mrc_filter(MRC *mrc, int binning, int kernel, float sigma) {

	float *data_array_src ;
	int	i, j,
		n, ni,
		n_w, w, n_h, h, t, off_w;
	int binningsize;
	int index;
	float f_val;

	int	maskindex=0,
		masksize = kernel*kernel,
		x=0,
		y=0;

	int	*indexes,
		*maskindexes;

	double  *maskData;

	w = mrc->header.nx;
	h = mrc->header.ny;
	n_w = w/binning;
	n_h = h/binning;
	off_w = w - n_w * binning;
	n=w*h;
	data_array_src = (float *)mrc->pbyData;
	maskData = malloc(sizeof(double)*masksize);
	maskindexes = malloc(sizeof(int)*masksize);
	indexes = malloc(sizeof(int)*binningsize);

	if (sigma !=0 && kernel % 2 == 1) {
		gaussianfiltermask(maskData, kernel, sigma);
	}

	for (i=-1,j=0,t=0,ni=0; t<n; t+=binning,j++) {
		if (j % n_w == 0) {
			j=0; i++;
			if (i>0)
				t += off_w+w*(binning-1);
		}
		if (ni>n_w*n_h)
			break;

		getMaskDataIndexes(maskindexes, kernel, t, w);
		for (f_val=0, index = 0; index < masksize; index++)
			if (maskindexes[index] != -1)
				f_val += data_array_src[maskindexes[index]] * maskData[index];

		data_array_src[ni] = f_val;
		ni++;

	}

	mrc->header.nx=n_w;
	mrc->header.ny=n_h;
	mrc_update_header(mrc);
	free(maskData);
	free(maskindexes);

}
/* }}} */

/* {{{ void mrc_binning(MRC *mrc, int binning, int skip_avg) */
void mrc_binning(MRC *mrc, int binning, int skip_avg) {

	float *data_array_src ;
	int	i, j,
		n, ni,
		n_w, w, n_h, h, t, off_w;
	int binningsize;
	int index;
	float f_val;
	int *indexes;

	if (binning>1) {
		
 		binningsize = binning*binning,
		indexes = malloc(sizeof(int)*binningsize);
		w = mrc->header.nx;
		h = mrc->header.ny;
		n_w = w/binning;
		n_h = h/binning;
                off_w = w - n_w * binning;
		n=w*h;
		data_array_src = (float *)mrc->pbyData;
                for (ni=0, i=-1,j=0,t=0; t<n; t+=binning,j++) {
                        if (j % n_w == 0) {
                                j=0; i++;
                                if (i>0)
                                        t += off_w+w*(binning-1);
                        }
			if (ni>n_w*n_h)
				break;

			if (skip_avg) {
				f_val = data_array_src[t];
			} else {
				getIndexes(indexes, binning, t, w) ;
				for (f_val=0, index=0; index<binningsize; index++)
					f_val += data_array_src[indexes[index]];
				f_val /= binningsize;
			}
			data_array_src[ni] = f_val;
			ni++;


			if (i>=(n_h-1) && j>=(n_w-1))
				break;
                }

		mrc->header.nx=n_w;
		mrc->header.ny=n_h;
		mrc_update_header(mrc);
		free(indexes);
	}
}
/* }}} */

/* {{{ void mrc_to_gd(MRC *mrc, int ** tpixels, int pmin, int pmax, int colormap) */
void mrc_to_gd(MRC *mrc, int ** tpixels, int pmin, int pmax, int colormap) {

	float	*data_array;
	float   fmin=mrc->header.amin,
			fmax=mrc->header.amax,
			scale = fmax - fmin,
			nmin, nmax,
			nscale,
			f_val;

	int	w=mrc->header.nx, h=mrc->header.ny,
		n=w*h,
		i,j,ij;
	int densitymax = (colormap) ? densityColorMAX : densityMAX;
	int gray = (colormap) ? 0 : 1;

    data_array = malloc(sizeof(float)*n);

    mrc_to_float(mrc, data_array);

	scale = fmax - fmin;
	nmin = fmin + pmin * scale / densitymax;
	nmax = fmin + pmax * scale / densitymax;
	nscale = nmax - nmin;

	if (nscale != 0)
		for (i = 0; i < w; ++i) {
			for (j = 0; j < h; ++j) {
				ij = i*h + j;
				f_val = data_array[ij];
				f_val = (f_val-nmin)*densitymax/nscale;
				tpixels[i][j] = setColorDensity(f_val, gray);
			}
		}

	free(data_array);
}
/* }}} */

/* {{{ void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int w, int h) */
void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int w, int h)
{
	int c;
	int x, y;
	int tox, toy;


        int     w_src, h_src, n_src,
		w_dst, h_dst, n_dst,
		x_min_src, x_max_src, y_min_src, y_max_src,
		x_min_dst, x_max_dst, y_min_dst, y_max_dst,
                i,j,ij,t;

	float	*data_array_src, *data_array_dst;

	w_src = w;
	h_src = h;
	n_src = w_src*h_src;

	w_dst = pmrc_dst->header.nx;
	h_dst = pmrc_dst->header.ny;
	n_dst = w_dst*h_dst;

	x_min_src = srcX;
	x_max_src = w;
	y_min_src = srcY;
	y_max_src = h;

	x_min_dst = dstX;
	x_max_dst = w_dst; 
	y_min_dst = dstY;
	y_max_dst = h_dst;

	x_min_src = srcX;
	x_max_src = x_min_src+w_src;
	y_min_src = srcY;
	y_max_src = y_min_src+h_src;

	x_min_dst = dstX;
	x_max_dst = x_max_src+dstX-srcX;
	y_min_dst = dstY;
	y_max_dst = y_max_src+dstY-srcY;

	if (0) {
	zend_printf("x_min_dst: %d ", x_min_dst);
	zend_printf("x_max_dst: %d ", x_max_dst);
	zend_printf("y_min_dst: %d ", y_min_dst);
	zend_printf("y_max_dst: %d ", y_max_dst);

	zend_printf("x_min_src: %d ", x_min_src);
	zend_printf("x_max_src: %d ", x_max_src);
	zend_printf("y_min_src: %d ", y_min_src);
	zend_printf("y_max_src: %d ", y_max_src);
	}
	data_array_src = (float *)pmrc_src->pbyData;
	data_array_dst = (float *)pmrc_dst->pbyData;

	int re, index=0;

	for (j=y_min_dst; j<y_max_dst; j++) {
		for (i=x_min_dst; i<x_max_dst; i++) {
			ij = i + j*w_dst;
			index = (i-x_min_dst+x_min_src)+(j-y_min_dst+y_min_src)*w;
			if (index<n_src && ij<n_dst && i<w_dst) {
				re = data_array_src[index];
				data_array_dst[ij]=re;
			}
		}
	}

}
/* }}} */

/* {{{ mrc_destroy(MRCPtr pmrc) */
void mrc_destroy(MRCPtr pmrc) {
	free(pmrc->pbyData);
	free(pmrc);
}
/* }}} */

/* {{{ mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars) */
void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars) {
        float   fmin=mrc->header.amin,
                fmax=mrc->header.amax,
                interval;
        float *data_array;

        int     h=mrc->header.nx, w=mrc->header.ny,
                n=w*h;
        int i, i1, i2, j, d;
        int mode=mrc->header.mode;
        int nb=0;

        interval=(fmax-fmin)/nb_bars;

        data_array = malloc(sizeof(float)*n);
        mrc_to_float(mrc, data_array);

        if(interval <= 0) {
                fmax = fmin = (float)data_array[0];
                for (i = 0; i<n ; i++) {
                        fmax = MAX(fmax, data_array[i]);
                        fmin = MIN(fmin, data_array[i]);
                }
                interval=(fmax-fmin)/nb_bars;
        }
        for (i=0; i<nb_bars; i++) {
                nb=0;
                for (d=0; d<n; d++) {
                        i1 = fmin+(i-1)*interval;
                        i2 = fmin+i*interval;
                        if (data_array[d] > i1 && data_array[d] <=i2)
                                nb++;
                }
                classes[i] = fmin + i*interval;
                frequency[i] = nb;
        }
        free(data_array);
}
/* }}} */

/* {{{ int getIndexes(int *indexes, int binning, int index, int imagewidth)
get pixel indexes from a  binning factor applied to a pixel index */
int getIndexes(int *indexes, int binning, int index, int imagewidth) {
	int	i=0,
		b_w=0,
		b_h=0;

	for(b_w=0; b_w<binning; b_w++)
                for(b_h=0; b_h<binning; b_h++, i++)
                        indexes[i] = index + b_w*imagewidth + b_h;
}
/* }}} */

/* {{{ int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth)
get pixel indexes from a mask (kernelxkernel) applied to a pixel index */
int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth) {
	int	i=0,
		m_w=0,
		m_h=0,
		max_size = imagewidth*imagewidth,
		max_index,
		ni,
		index_row = index/imagewidth;

	for(m_w=0; m_w<kernel; m_w++) {
                for(m_h=0; m_h<kernel; m_h++, i++) {
                        indexes[i] = index + m_w*imagewidth + m_h;
                        ni = index + m_w * imagewidth + m_h;
                        max_index  = imagewidth * (index_row + m_w + 1);
                        if (ni >= max_index  || max_index  > max_size )
                                ni = -1;
                        indexes[i] = ni;
                }
        }
}
/* }}} */

/* {{{ int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader) */
int gdreadMRCHeader(gdIOCtx *io_ctx, MRCHeader *pMRCHeader) {

	gdGetBuf(pMRCHeader, MRC_HEADER_SIZE, io_ctx);
	if(	(pMRCHeader->nx < 0) || (pMRCHeader->ny < 0) || 
		(pMRCHeader->nz < 0) || (pMRCHeader->mode < 0) || 
		(pMRCHeader->mode > 4) || (pMRCHeader->x_length < 0) ||
		(pMRCHeader->y_length < 0) || (pMRCHeader->z_length < 0) ||
		(pMRCHeader->x_length > pMRCHeader->nx ) ||
		(pMRCHeader->y_length > pMRCHeader->ny ) ||
		(pMRCHeader->z_length > pMRCHeader->nz ) 
	)
			return -1; /* This is not a valid pMRCHeader header */
	return 1 ;
}
/* }}} */

/* {{{ int gdreadMRCData(gdIOCtx *io_ctx, MRC *pMRC) */
int gdreadMRCData(gdIOCtx *io_ctx, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}
	

	if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
		pMRC->pbyData = malloc(uElements*uElementSize);

	gdGetBuf(pMRC->pbyData, (uElements*uElementSize), io_ctx);
	
	return 1;
}
/* }}} */

/* {{{ int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC) */
int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;

	if (gdreadMRCHeader(io_ctx, &(pMRC->header))==-1)
		return -1;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}
	

	if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
		pMRC->pbyData = malloc(uElements*uElementSize);

	gdGetBuf(pMRC->pbyData, (uElements*uElementSize), io_ctx);
	
	return 1;
}
/* }}} */

/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
 */
