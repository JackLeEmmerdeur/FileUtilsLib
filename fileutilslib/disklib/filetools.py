from enum import Enum
from math import floor, log
from os import statvfs_result
from os.path import realpath, ismount, dirname
from typing import Dict


class FileSizes(Enum):
	TB_BYTE_SIZE = 1024 * 1024 * 1024 * 1024
	GB_BYTE_SIZE = 1024 * 1024 * 1024
	MB_BYTE_SIZE = 1024 * 1024


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
