from optparse import OptionParser
import sys

parser = OptionParser()

parser.add_option('-v', '--version', action='store_true', dest='version',
                  help="get version information")
parser.add_option('-s', '--session', action='store', dest='session',
                  help="name of existing session to continue")
parser.add_option('-i', '--instruments', action='store', dest='pyscopehosts',
                  help="comma separated list of pyscope hosts")
parser.add_option('-l', '--launchers', action='store', dest='launcherhosts',
                  help="comma separated list of launchers")
parser.add_option('-p', '--prevapp', action='store_true', dest='prevapp',
                  help="restart previous application")

(options, args) = parser.parse_args()

if options.version:
	import version
	print 'Leginon version: %s' % (version.getVersion(),)
	print '   Installed in: %s' % (version.getInstalledLocation(),)
	sys.exit()

