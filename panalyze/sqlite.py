from pysqlite2 import dbapi2 as sqlite

def connect(filename):
	con = sqlite.connect(filename)

	con.execute('create table if not exists log_line (text, datetime, pid, line_number, duration, line_type, statement_type)')
	return con

def prep_line(log_line):
	return (
	        log_line.datetime,
	        log_line.pid,
	        log_line.line_number,
	        log_line.duration,
	        log_line.line_type,
	        log_line.statement_type)

write_counter = 0

def write_log_line(con, log_line):
	global write_counter
	con.execute('insert into log_line (datetime, pid, line_number, duration, line_type, statement_type) values (?, ?, ?, ?, ?, ?)', prep_line(log_line))
	write_counter += 1
	if write_counter > 5000:
		con.commit()
		write_counter = 0
