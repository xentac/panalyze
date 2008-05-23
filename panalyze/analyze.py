import panalyze.parser

def combine_durations(dbcon):
	cur = dbcon.cursor()

	cur.execute("select text, datetime, pid, line_number, duration, line_type, statement_type from log_line where statement_type = 'duration'")
	for duration_line in cur:
		print duration_line
		log_line = panalyze.parser.LogLine(*duration_line)
		print log_line
		duration = log_line.parse_duration()
		dbcon.execute("update log_line set duration = ? where pid = ? and line_number = ?", (duration, log_line.pid, log_line.line_number - 1))
		dbcon.execute("delete from log_line where pid = ? and line_number = ?", (log_line.pid, log_line.line_number))
		print "deleted"

def categorize_lines(lines):
	processes = {}
	dates = {}
	
	for line in lines:
		processes.setdefault(line.pid, {}).setdefault(line.line_number, line)
		dates.setdefault(line.datetime, []).append(line)

	return processes, dates
