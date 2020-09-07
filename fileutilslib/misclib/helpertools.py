from sys import exc_info
from traceback import format_exception
from typing import Any, List, Union
from six import string_types, text_type
from sys import platform
from inspect import isbuiltin, ismethod
from fileutilslib.classes.ConsoleColors import ConsoleColors, ConsoleColor


def is_linux():
	return platform == "linux"


def is_function(var: Any) -> bool:
	return isbuiltin(var) or hasattr(var, '__call__')  # isfunction(var)


def is_method(var: Any) -> bool:
	return ismethod(var)


def is_boolean(var: Any) -> bool:
	return isinstance(var, bool)


def is_string(var: Any) -> bool:
	return isinstance(var, string_types)


def is_stringtype(obj: Any) -> bool:
	return is_unicode(obj) or is_string(obj)


def is_integer(var: Any) -> bool:
	return isinstance(var, int)


def is_integerish(var: Any) -> bool:
	"""stackoverflow.com/questions/1265665/python-check-if-a-string-represents-an-int-without-using-try-except"""
	i = str(var)
	return i == '0' or (i if i.find('..') > -1 else i.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


def is_unicode(obj: Any) -> bool:
	return isinstance(obj, text_type)


def is_sequence(var: Any) -> bool:
	return (
		not hasattr(var, "strip") and
		hasattr(var, "__getitem__") or
		hasattr(var, "__iter__")
	)


def is_sequence_with_any_elements(tuple_or_list: Union[list, set, dict, range, frozenset, tuple, bytearray]) -> bool:
	if is_sequence(tuple_or_list) and len(tuple_or_list) > 0:
		return True
	return False


def is_empty_sequence(sequencevar: Union[list, set, dict, range, frozenset, tuple, bytearray]) -> bool:
	return not is_sequence(sequencevar) or len(sequencevar) == 0


def is_dict(var: Any) -> bool:
	return isinstance(var, dict)


def is_empty_dict(var: dict) -> bool:
	if var is None:
		return True
	a = not isinstance(var, dict)
	b = (len(var) == 0)
	return a and b


def list_to_str(
		srclist: List[Any],
		div: str = ", ",
		use_prosaic: bool=False,
		prosaic_terminator: str="or",
		prepend_to_list_item=None,
		append_to_list_item=None
):
	t = ""

	if not is_sequence(srclist):
		return t

	c = len(srclist) - 1

	if c < 0:
		return t

	for (index, a) in enumerate(srclist):
		if index > 0:
			if use_prosaic:
				if index < c:
					t += div
				else:
					t += prosaic_terminator

			else:
				if index <= c:
					t += div

		if prepend_to_list_item is not None:
			t += prepend_to_list_item
		t += a
		if append_to_list_item is not None:
			t += append_to_list_item

	return t


def assert_obj_has_keys(obj: object, objtype: str, keys: List[str]):
	if obj is None or type(obj) is not dict:
		raise Exception("obj is not of type dict")
	if keys is None or len(keys) == 0:
		raise Exception("no obj")
	for key in keys:
		if key not in obj:
			raise Exception("Missing key '{}' in object({})".format(key, objtype))


def fill(fillchar: str, filllen: int) -> str:
	s = ""
	for i in range(0, filllen):
		s += fillchar
	return s


def fill_left(targetstr: str, fillchar: str, maxfill_len: int):
	if string_is_empty(targetstr):
		return fill(fillchar, maxfill_len)
	tl = len(targetstr)
	if tl >= maxfill_len:
		return targetstr
	fl = maxfill_len - tl
	n = int(fl / len(fillchar))
	pad = ""
	for i in range(0, n):
		pad += fillchar
	return pad + targetstr


def string_equal_utf8(obj1, obj2, case_sensitive=True):
	f1n = obj1 is None
	f2n = obj2 is None

	if f1n and f2n:
		return True
	elif f1n or f2n:
		return False
	else:
		f1u = is_unicode(obj1)
		f2u = is_unicode(obj2)
		f1s = is_string(obj1)
		f2s = is_string(obj2)

		if not f1s and not f1u:
			obj1 = str(obj1)
		if not f2s and not f2u:
			obj2 = str(obj2)

		if f1u and f2u:
			eq = string_equal(obj1, obj2, case_sensitive)
		elif f1u and not f2u:
			eq = string_equal(obj1, decode(obj2, "utf-8"), case_sensitive)
		else:
			eq = string_equal(decode(obj1, "utf-8"), obj2, case_sensitive)
		return eq


def string_equal(str1, str2, case_sensitive=True):
	if case_sensitive:
		return str1 == str2
	# Do not call string_iequal here (method-call-micro-optimized)
	e1 = string_is_empty(str1)
	e2 = string_is_empty(str2)
	if e1 and e2:
		return True
	elif e1 or e2:
		return False
	else:
		if str1.lower() == str2.lower():
			return True
		else:
			return False


def repeat(text: str, times: int):
	t = ""
	for i in range(0, times):
		t += text
	return t


def strip(text):
	return text.lstrip().rstrip()


def get_reformatted_exception(msg, exc, print_stack=True) -> str:
	tb = ""
	excfmtlist = format_exception(type(exc), exc, exc_info()[2], 1 if print_stack is False else None)

	if print_stack is False:
		tb = excfmtlist[len(excfmtlist) - 1]
	else:
		for (index, excfmtitem) in enumerate(excfmtlist):
			if index > 0:
				tb += "\r\n"
			tb += excfmtitem
	return "{}\r\n{}".format(msg, tb)


def string_is_empty(
	thetext: string_types,
	preserve_whitespace: bool=False,
	check_strip_availability: bool=False
) -> bool:
	"""
	Checks if `thetext` is emtpy and returns True if so.

	Example:
	>>> string_is_empty("  ")
	True
	>>> string_is_empty("  ", True)
	False
	>>> string_is_empty("  ", False)
	True

	:param thetext: The string to check for emptiness
	:param preserve_whitespace: If True, blankspaces will not count as empty
	:param check_strip_availability: Checks if `thetext is a string-type via availability of strip-method (esotheric)
	:return: True if `thetext` is empty
	:rtype: bool
	"""
	if thetext is None:
		return True
	isstring = False
	if check_strip_availability:
		isstring = hasattr(thetext, "strip")
	elif is_string(thetext) or is_unicode(thetext):
		isstring = True
	if isstring or isinstance(thetext, bytes):
		return len(thetext if preserve_whitespace else thetext.strip()) < 1
	else:
		return True


def find_char_backwards(textstr, charstr, pos):
	c = None
	for (idx, s) in enumerate(reversed(textstr)):
		if idx > pos:
			if c is None:
				c = 0
			c += 1
			if s == charstr:
				c -= 1
				break
	return c


def humantime(secs: int) -> str:
	fs = lambda ts: fill_left(ts, "0", 2)

	if secs < 60:
		return str(int(secs)) + " sec"
	elif secs < 3600:
		m = int(secs / 60)
		s = int(secs % 60)
		return "{}:{} min".format(fs(str(m)), fs(str(s)))
	else:
		h = int(secs / 3600)
		rsecs = secs % 3600
		m = int(rsecs / 60)
		s = int(rsecs % 60)
		return "{}:{}:{} hr".format(fs(str(h)), fs(str(m)), fs(str(s)))


def singlecharinput(msg, color: ConsoleColors):
	nmsg = None

	if color is not ConsoleColors.NONE:
		nmsg = ConsoleColor.colorline(
			msg + " ",
			color
		)
	else:
		nmsg = msg

	return strip(input(nmsg)).lower()
