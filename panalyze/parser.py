import re
import datetime

import panalyze.sqlite

log_line_re = re.compile(r'(\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d) ... \[(\d+)\]: \[(\d*)-1\] (LOG|ERROR|HINT|WARNING|STATEMENT):\s*(.*)')

class LogLine(object):
	text = None
	datetime = None
	pid = None
	line_number = None
	duration = None
	line_type = 'LOG'
	statement_type = None

	def __init__(self, text=None, datetime=None, pid=None, line_number=None, duration=None, line_type='LOG', statement_type=None):
		self.text = text
		self.datetime = datetime
		self.pid = pid
		self.line_number = line_number
		self.duration = duration
		self.line_type = line_type
		self.statement_type = statement_type

	def parse_duration(self):
		if self.statement_type == 'duration':
			return float(self.text.split(' ')[-2])
		return None

class StderrParser(object):
	filename = None
	fp = None

	def __init__(self, filename, dbcon):
		self.dbcon = dbcon
		self.fp = open(filename)
		self.filename = filename

	def parse_file(self):
		self.fp.seek(0)

		line_dict = {}
		last_line = None
		for line_count, line in enumerate(self.fp):
			if line_count != 0 and line_count % 1000000 == 0:
				print "Processed %d lines" % line_count

			m = log_line_re.match(line)
			if m:
				text = line.strip()
				pid = int(m.group(2))
				line_number = int(m.group(3))
				statement_type = None
				if m.group(4) == 'LOG':
					statement_type = m.group(5).split(' ',1)[0][:-1]
				if statement_type == 'duration':
					previous_line_number = line_number-1
					if line_dict.get(pid, None):
						if pid == 9:
							print line
						previous_log_line = line_dict[pid].get(previous_line_number, None)
						if previous_log_line:
							previous_log_line.duration = float(text.split(' ')[-2])
						for old_line_number, old_line in line_dict[pid].iteritems():
							panalyze.sqlite.write_log_line(self.dbcon, old_line)
						line_dict[pid] = {}
					continue
				last_line = LogLine(text, datetime.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S'), pid, line_number, None, m.group(4), statement_type=statement_type)
				line_dict.setdefault(last_line.pid, {}).setdefault(last_line.line_number, last_line)
			else:
				last_line.text += line.strip()

		# Finish writing the last lines
