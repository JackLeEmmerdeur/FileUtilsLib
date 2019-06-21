from fileutilslib.misclib.helpertools import humantime, strip


def parse_dd_info(line):
	bytestrpos = line.find(" ")
	bytestr = strip(line[0:bytestrpos])
	byteint = int(bytestr)
	brackpos = line.find(")")
	tmstartpos = line.find(",", brackpos)
	nextcommapos = line.find(",", tmstartpos + 1)
	charbeforecomma = line[nextcommapos-1:nextcommapos]
	if charbeforecomma == "s" or charbeforecomma == "m" or charbeforecomma == "h":
		tm = strip(line[tmstartpos+1:nextcommapos])
	else:
		nextnextcommapos = line.find(",", nextcommapos + 1)
		tm = strip(line[nextcommapos-2:nextnextcommapos])

	tm_comma_pos = tm.find(",")
	is_secs = "s" in tm
	is_mins = "m" in tm
	is_hours = "h" in tm
	is_commatime = False

	if is_mins or is_hours:
		if tm_comma_pos > -1:
			tm_1 = tm[0:tm_comma_pos].strip()
			tm_2 = float("0." + tm[tm_comma_pos+1:].strip("m" if is_mins else "h").strip())
			if is_mins:
				factor = 60
			else:
				factor = 3600
			tm_1 = int(tm_1) * factor
			tm_2 = int(tm_2 * factor)
			tm = tm_1 + tm_2
			is_commatime = True

	if is_commatime is False:
		if is_secs:
			if tm_comma_pos > -1:
				tm = int(tm[0:tm_comma_pos])
			else:
				tm = int(tm.strip("s").strip())
		elif is_mins:
				tm = int(tm.strip("m").strip()) * 60
		elif is_hours:
				tm = int(tm.strip("m").strip()) * 60

	return {
		"size_b": byteint,
		"time": int(tm),
		"time_h": humantime(tm)
	}
