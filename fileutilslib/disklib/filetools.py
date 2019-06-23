from enum import Enum
from math import floor, log
from os import statvfs_result
from os.path import realpath, ismount, dirname
from fileutilslib.misclib.helpertools import string_is_empty, strip
from typing import Dict
from os import sep
from pathlib import Path
from plumbum import local
from fileutilslib.misclib.helpertools import singlecharinput
from fileutilslib.classes.ConsoleColors import ConsoleColor, ConsoleColors


class FileSizes(Enum):
	TB_BYTE_SIZE = 1024 * 1024 * 1024 * 1024
	GB_BYTE_SIZE = 1024 * 1024 * 1024
	MB_BYTE_SIZE = 1024 * 1024


def sevenzip(interactive: bool, compress_type: str, inputfilepath: str, outputfilepath: str=None):
	if string_is_empty(inputfilepath):
		raise Exception("No input file path provided")

	if string_is_empty(compress_type):
		if interactive is True:
			compress_type = strip(
				input(
					"Type the name of the compression algorithm (7z or zip)\n"
				)
			).lower()
		else:
			compress_type = "zip"

	if string_is_empty(compress_type):
		raise Exception("No compression algorithm chosen")

	if compress_type != "zip" and compress_type != "7z":
		raise Exception("Wrong compression algorithm (use 7z or zip)")

	if string_is_empty(outputfilepath):
		if interactive is True:
			outputfilepath = strip(input("Type the path of the compressed image file\n"))
		else:
			outputfilepath = inputfilepath + "." + compress_type

	if string_is_empty(outputfilepath):
		raise Exception("File path empty")

	cancelled = False

	p = Path(outputfilepath)

	if p.exists():
		yn = singlecharinput(
			"The file '{}' exists. Do you want to delete it?".format(
				outputfilepath
			), ConsoleColors.WARNING
		)
		if yn == "n":
			cancelled = True
			print(ConsoleColor.colorline("Cancelling compress process", ConsoleColors.OKBLUE))
		else:
			print(ConsoleColor.colorline("Deleting '{}'".format(outputfilepath), ConsoleColors.FAIL))
			if Path(outputfilepath).exists():
				print(ConsoleColor.colorline(
					"Could not delete '{}'".format(
						outputfilepath
					), ConsoleColors.FAIL)
				)
				cancelled = True

	if cancelled is False:
		sz = local["7z"]
		sz.run(["a", str(p.absolute()), inputfilepath])


def is_directory_path(path: str):
	if not string_is_empty(path):
		c = len(path)
		return strip(path)[c-1:c] == sep
	return False


def sizeinfo_from_statvfs_result(statvfs_res: statvfs_result) -> Dict:
	d = dir(statvfs_res)

	if "f_bsize" not in d or "f_blocks" not in d or "f_bavail" not in d:
		raise Exception("Not a valid statvfs_result")

	bs = statvfs_res.f_bsize
	total = statvfs_res.f_blocks * bs
	free = statvfs_res.f_bavail * bs
	used = total - free
	return {
		"total": total,
		"total_h": bytes_to_unit(total, True),
		"free": free,
		"free_h": bytes_to_unit(free, True),
		"used": used,
		"used_h": bytes_to_unit(used, True)
	}


def find_mount_point(pathstr: str) -> str:
	# credit: Fred Foo
	# https://stackoverflow.com/questions/4453602/how-to-find-the-mountpoint-a-file-resides-on
	path = realpath(pathstr)
	while not ismount(path):
		path = dirname(path)
	return path


def bytes_to_unit(bytesize: int, base1024: bool=False, print_suffix: bool=True, print_space: bool=True):
	"""
	Converts bytes to a string in another unit with an appropriate suffix
	:param bytesize: The amount of bytes you want to convert
	:param base1024: If the calculation should be made with 1024 bytes or 1000 bytes for one kilobyte
	:param print_suffix: Print a unit suffix (e.g. KB)
	:param print_space: Print a space between number and suffix
	:return: A localized number String (commata/digits after comma)
	"""
	size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	basefactor = 1024 if base1024 else 1000

	if bytesize > 0:

		index = int(floor(log(bytesize, basefactor)))
		unitdivisor = pow(basefactor, index)
		bytes_in_unit = round(bytesize / unitdivisor, 2)

		if print_suffix:
			return "{}{}{}".format(bytes_in_unit, " " if print_space else "", size_name[index])
		else:
			return "{}".format(bytes_in_unit)
	else:
		return "0 Bytes"


def get_filesize_progress_divider(total_size: int):
	tb = total_size / 1000000000000
	gb = total_size / 1000000000
	mb = total_size / 1000000
	kb = total_size / 10000

	if tb > 1:
		d = 10000000000
	elif gb > 1:
		if gb >= 5:
			d = 50000000
		else:
			d = 10000000
	elif mb > 1:
		d = 500000
	elif kb > 1:
		if kb > 100:
			d = 50000
		else:
			d = 1000
	else:
		d = 10

	return d
