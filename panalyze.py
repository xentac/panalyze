#!/usr/bin/env python

import panalyze.parser
import panalyze.analyze
import panalyze.sqlite
import panalyze.pcurses

import sys

from optparse import OptionParser

def _main(argv=None):

	if argv == None:
		argv = sys.argv

	parser = OptionParser()

	parser.add_option('-i', '--init', dest='initdb', help="initialize panalyze db", action="store_true", default=False)
	parser.add_option('-f', '--file', dest='log_filename', help="parse FILE", metavar="FILE", action="append")
	parser.add_option('-d', '--dbfile', dest='db_filename', help="store log info in FILE sqlite db", metavar="FILE")
	parser.add_option('-l', '--log', dest='logview', help="view the queries in a log viewer", action="store_true", default=False)

	(options, args) = parser.parse_args(argv)

	if not options.initdb and not options.logview:
		parser.error("must choose -i or -l")

	if options.initdb:
		if options.log_filename is None:
			parser.error("at least one log file is required")

		if options.db_filename is None:
			parser.error("must specify a sqlite db")

		dbcon = panalyze.sqlite.connect(options.db_filename)

		for log_filename in options.log_filename:
			parser = panalyze.parser.StderrParser(log_filename, dbcon)
			parser.parse_file()

		dbcon.commit()

	elif options.logview:
		if options.db_filename is None:
			parser.error("must specify a sqlite db")

		import curses

		dbcon = panalyze.sqlite.connect(options.db_filename)

		curses.wrapper(panalyze.pcurses.main_curses)

	return 0

if __name__ == '__main__':
	sys.exit(_main())
