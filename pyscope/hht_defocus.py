#!/usr/bin/env python
import sys
from pyscope import hitachi

from pyscope import instrumenttype
search_for = 'TEM'
try:
	h = instrumenttype.getInstrumentTypeInstance(search_for)
	if h.__class__.__name__ not in ('Hitachi','HT7800'):
		raise ValueError("TEM %s is not of Hitachi subclass" % h.__class__.__name__)
except Exception, e:
	print "Error", e
	sys.exit(1)

focus_offset_file = hitachi.configs['defocus']['focus_offset_path']
try:
	h.findMagnifications()
except (RuntimeError,IOError):
	# RuntimeError of not finding zero_defocus is exactly what this script is doing.
	pass

if h.zero_defocus_current:
	answer = raw_input('Aready has a focus_offset file. Do you really want to redo this ? Y/N/y/n ')
	if 'n' in answer.lower():
		sys.exit(0)
mag0 = h.getMagnification()
mags = h.getMagnifications()
offsets = []
for m in mags:
	h.setMagnification(m)
	foc = h.getFocus()
	offsets.append(foc)
h.setMagnification(mag0)
submode_names = h.getOrderedProjectionSubModeNames()
submode_map=h.getProjectionSubModeMap()
u_focus = {}
for name in submode_names:
	item_name = 'ref_magnification'
	ref_mag = hitachi.configs['defocus'][item_name][name.lower()]
	if not ref_mag in mags:
		raise ValueError('Reference magnification %s not a valid magnification' % (ref_mag,))
	ref_mag_index = mags.index(ref_mag)
	ref_zero = offsets[ref_mag_index]
	h.saveEucentricFocusAtReference(name,ref_zero)
	u_focus[name] = ref_zero
print mags
print offsets
df = open(focus_offset_file,'w')
for i,m in enumerate(mags):
	mode_name, mode_id = submode_map[m]
	defocus = offsets[i] - u_focus[mode_name]
	df.write('%d\t%9.6f\n' % (m, defocus))
df.close()
	
	

