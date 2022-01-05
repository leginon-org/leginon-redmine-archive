#!/usr/bin/env python
from dbschema.info_tools import export_targets
from dbschema.info_tools import export_ice
from dbschema.info_tools import export_ctf
from dbschema.info_tools import export_child_paths

if __name__=='__main__':
	session_name = raw_input('Which session ? ')
	base_path = raw_input('Where to save under ? (default: ./%s) ' % session_name)
	if not base_path:
		base_path = './%s' % session_name
	app_target = export_targets.TargetExporter(session_name, base_path)
	app_ice = export_ice.IceThicknessExporter(session_name, base_path)
	app_ctf = export_ctf.CtfExporter(session_name, base_path)
	app_image = export_child_paths.ChildImagePathExporter(session_name, base_path)
	app_target.run()
	app_ice.run()
	app_ctf.run()
	print('All Done! Saved in %s' % (base_path,))
