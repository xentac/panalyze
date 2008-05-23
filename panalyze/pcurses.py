import curses
import datetime
import math

class CursesList(object):
	row = 0
	top_visible_row = 0
	dbcon = None

	durations = [None, None, None]
	highest_duration = [None, None, None]

	zoom = 0

	ZOOM_SECOND = 0
	ZOOM_MINUTE = 1
	ZOOM_HOUR = 2
	
	def __init__(self, dbcon):
		self.dbcon = dbcon

	def find_highest_duration(self, zoom):
		if self.highest_duration[zoom] is None:
			self.highest_duration[zoom] = reduce(lambda x, y: (None, x[1]) if x[1] > y[1] else (None, y[1]), self.durations[zoom])[1]
		return self.highest_duration[zoom]

	def fill_second_durations(self):
		if self.durations[0] is None:
			cur = self.dbcon.cursor()

			cur.execute("select datetime, sum(duration) as sm from log_line group by datetime having sm is not null")

			self.durations[0] = [(datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'), float(row[1])) for row in cur.fetchall()]

	def fill_durations(self, zoom):
		if zoom == self.ZOOM_MINUTE and not self.durations[1]:
			minute_dict = {}
			for row in self.durations[0]:
				minute_time = row[0].replace(second=0, microsecond=0)
				minute_dict.setdefault(minute_time, 0)
				minute_dict[minute_time] += row[1]

			minutes = sorted(minute_dict.keys())
			self.durations[1] = [(minute, minute_dict[minute]) for minute in minutes]
		elif zoom == self.ZOOM_HOUR and not self.durations[2]:
			hour_dict = {}
			for row in self.durations[0]:
				hour_time = row[0].replace(minute=0, second=0, microsecond=0)
				hour_dict.setdefault(hour_time, 0)
				hour_dict[hour_time] += row[1]

			hours = sorted(hour_dict.keys())
			self.durations[2] = [(hour, hour_dict[hour]) for hour in hours]

	def get_durations(self, zoom):
		self.fill_second_durations()
		if zoom != 0:
			self.fill_durations(zoom)
		return self.durations[zoom]

	def draw_row(self, scr, row_num):
		# figure out what data should be shown on that row
		durations = self.get_durations(self.zoom)
		if len(durations) > row_num:
			row = durations[row_num+self.top_visible_row]
		else:
			scr.addstr(row_num, 0, '')
			return

		# draw row
		first_string = "%s: %10.2f " % (row[0], row[1])

		maxx = scr.getmaxyx()[1]

		#f = open('file', 'w')
		#f.write('%d\n' % row[1])
		#f.write('%d\n' % self.find_highest_duration(self.zoom))
		#f.write('%d\n' % maxx)
		#f.write('%d\n' % len(first_string))
		#f.write('%r\n' % row[1])
		#f.write('%s\n' % type(row[1]))
		#f.write('%s\n' % type(self.find_highest_duration(self.zoom)))
		#f.write('%f\n' % (row[1]/self.find_highest_duration(self.zoom)))
		#f.write('%f\n' % (row[1]/self.find_highest_duration(self.zoom)*10))
		#f.write('%f\n' % (math.log10(row[1]/self.find_highest_duration(self.zoom)*10)))
		#f.write('%d\n' % int(math.log(row[1], self.find_highest_duration(self.zoom)) * (maxx - len(first_string) - 1)))
		graphpoints = int(math.log(row[1], self.find_highest_duration(self.zoom)) * (maxx - len(first_string) - 1))
		#graphpoints = int((row[1]/self.find_highest_duration(self.zoom)) * (maxx - len(first_string) - 1))
		graph_string = 'X'*graphpoints

		scr.addstr(row_num, 0, first_string + graph_string, 0 if row_num != self.row - self.top_visible_row else curses.A_STANDOUT)

	def draw(self, scr):
		scr.clear()

		for row_num in range(0, scr.getmaxyx()[0]):
			self.draw_row(scr, row_num)

	def move_row(self, scr, steps):
		last_row = self.row
		self.row = self.row + steps
		if self.row < 0:
			self.row = 0
		if self.row >= len(self.durations[self.zoom]):
			self.row = len(self.durations[self.zoom])-1

		maxy = scr.getmaxyx()[0]
		if self.row - self.top_visible_row >= maxy:
			self.top_visible_row += self.row - self.top_visible_row - maxy + 1
			if abs(steps) > 1:
				self.draw(scr)
				scr.refresh()
			else:
				scr.scroll(1)
				self.draw_row(scr, maxy-2)
				self.draw_row(scr, maxy-1)
		elif self.row < self.top_visible_row:
			self.top_visible_row -= self.top_visible_row - self.row
			if abs(steps) > 1:
				self.draw(scr)
				scr.refresh()
			else:
				scr.scroll(-1)
				self.draw_row(scr, 0)
				self.draw_row(scr, 1)
		else:
			self.draw_row(scr, last_row - self.top_visible_row)
			self.draw_row(scr, self.row - self.top_visible_row)

	def change_zoom(self, scr, steps):
		self.zoom += steps
		if self.zoom < 0:
			self.zoom = 0
		elif self.zoom > 2:
			self.zoom = 2
		self.row = 0
		self.top_visible_row = 0
		self.draw(scr)
		scr.refresh()

def main_curses(stdscr, dbcon):
	stdscr.scrollok(1)
	stdscr.idlok(1)
	curses_list = CursesList(dbcon)
	curses_list.draw(stdscr)
	stdscr.refresh()
	while 1:
		c = stdscr.getch()
		if c == ord('q'): break  # Exit the while()
		elif c == curses.KEY_DOWN: curses_list.move_row(stdscr, 1)
		elif c == curses.KEY_UP: curses_list.move_row(stdscr, -1)
		elif c == curses.KEY_NPAGE: curses_list.move_row(stdscr, stdscr.getmaxyx()[0])
		elif c == curses.KEY_PPAGE: curses_list.move_row(stdscr, -1 * stdscr.getmaxyx()[0])
		elif c == curses.KEY_HOME:
			curses_list.change_zoom(stdscr, -1)
		elif c == curses.KEY_END:
			curses_list.change_zoom(stdscr, 1)
