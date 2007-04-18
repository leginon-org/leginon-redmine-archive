#!/bin/bash

rm -fv `find .. -name "*.py[oc]"`
rm -frv selexlocal


selexon.py \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00002en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00003en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00004en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00005en_00.mrc \
  07jan05b_00012gr_00001sq_v01_00002sq_00_00006en_00.mrc \
  range=0,180,235 templateIds=57 \
  outdir=. diam=140 lp=0 bin=8 overlapmult=2 \
  runid=selexlocal  thresh=0.45 method=. commit
