/*
  +----------------------------------------------------------------------+
  | PHP Extension to read MRC file format as a gd image resource         |
  +----------------------------------------------------------------------+
  | Author: D. Fellmann                                                  |
  +----------------------------------------------------------------------+
*/

/* gd image resource */
static int le_gd; 

void mrc_to_histogram(MRC *mrc, int *frequency, float *classes, int nb_bars);
void mrc_to_float(MRC *mrc, float *pdata_array);

/* return pixel indexes to average for binning */
int getIndexes(int *indexes, int binning, int index, int imagewidth);
int getMaskDataIndexes(int *indexes, int kernel, int index, int imagewidth); 

int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC);
int gdreadMRCData(gdIOCtx *io_ctx, MRC *pMRC);
int gdloadMRC(gdIOCtx *io_ctx, MRC *pMRC);

void mrc_copy(MRC *mrc_src, MRC *mrc_dst, int x1, int y1, int x2, int y2);
void mrc_copy_to(MRCPtr pmrc_dst, MRCPtr pmrc_src, int dstX, int dstY, int srcX, int srcY, int w, int h);
MRCPtr mrc_create(int x_size, int y_size);
void mrc_destroy(MRCPtr pmrc);
void mrc_to_gd(MRC *mrc, int ** tpixels, int pmin, int pmax, int colormap);
