from pathlib import Path
from plumbum import local
from os import remove, statvfs, stat
from subprocess import PIPE
from datetime import datetime
from typing import Dict, Callable
from fileutilslib.disklib.fdisktools import fdisklist, fdiskdevicesize, predict_job_time
from fileutilslib.misclib.helpertools import string_equal_utf8, strip, string_is_empty, humantime, singlecharinput
from fileutilslib.disklib.filetools import sizeinfo_from_statvfs_result, find_mount_point, bytes_to_unit, is_directory_path
from fileutilslib.disklib.ddtools import parse_dd_info
from fileutilslib.classes.ConsoleColors import ConsoleColors, ConsoleColor


class ImageBackup:
	_devicepath = None
	""":type: Path"""

	_imagepath = None
	""":type: Path"""

	_device_ok = None
	""":type: bool"""

	_devices = None
	""":type: List[object]"""

	def __init__(self, list_devices: bool = False):
		self._device_ok = False
		self._devices = fdisklist(list_devices)

	def assert_devicepath_is_valid(self) -> None:
		if self._devicepath is None or not self._devicepath.exists():
			raise Exception("Devicepath is invalid")

	def assert_imagepath_is_valid(self) -> None:
		if self._imagepath is None:
			raise Exception("Imagepath not set")

	def assert_free_space(self, safe_free_targetspace_margin: int=None) -> None:
		sf = safe_free_targetspace_margin
		sf = 0 if (sf is None or sf < 0) else sf

		if self.get_image_mountpoint_sizeinfo()[
			"free"] - sf <= self.get_target_image_sizebytes():
			raise Exception("There is not enough free space to create the image")

	def print_pre_dd_info(self):
		print(ConsoleColor.colorline(
			"Approximate image size: {}".format(self.get_target_image_sizehuman()),
			ConsoleColors.UNDERLINE))

		print(ConsoleColor.colorline(
			"Free space on image partition: {}".format(self.get_image_mountpoint_sizeinfo()["free_h"]),
			ConsoleColors.UNDERLINE))

	def get_devicepath(self) -> str:
		return Path(self._device_str)

	def get_target_image_sizehuman(self) -> str:
		return bytes_to_unit(self.get_target_image_sizebytes(), True, True, False)

	def get_target_image_sizebytes(self) -> str:
		return fdiskdevicesize(self._devices, str(self._devicepath.absolute()))

	def image_exists(self) -> bool:
		return self._imagepath is not None and self._imagepath.exists()

	def ensure_image_deleted(self, force_delete=False) -> None:
		if self.image_exists():
			image = None
			yn = "n"

			if force_delete is True:
				yn = "y"
			else:
				print(ConsoleColor.colorline("The image already exists", ConsoleColors.FAIL))
				yn = singlecharinput(
					"Do you want to really delete the existing image file (y/n)?",
					ConsoleColors.OKGREEN
				)

			if yn == "y":
				if force_delete is False:
					print(
						ConsoleColor.colorline("Deleting image '{}'".format(str(self._imagepath)), ConsoleColors.FAIL))

				imagefilepath = str(self._imagepath.absolute())
				remove(imagefilepath)
				image = Path(str(imagefilepath))

				if image.exists():
					raise Exception("Could not delete image '{}'".format(imagefilepath))
				else:
					self._imagepath = image

	def get_image_mountpoint_sizeinfo(self) -> Dict:
		image_mountpoint = find_mount_point(str(self._imagepath))
		return sizeinfo_from_statvfs_result(statvfs(image_mountpoint))

	def get_imagepath(self) -> Path:
		return self._imagepath

	def set_image_path(self, image_path: str = None) -> bool:
		is_dir_msg = "Image path '{}' is not accepted, as it is a directory!"

		is_dir = False

		if not string_is_empty(image_path):
			if is_directory_path(image_path):
				is_dir = True
			else:
				self._imagepath = Path(image_path)
				return True
		else:
			imagepathok = False
			imagefile = None

			try:
				while imagepathok is False:
					fpi = input("Type the filepath of the image you want to create (empty to cancel image creation):\n")
					imagefilepath = strip(fpi)

					if string_is_empty(imagefilepath):
						raise Exception("_cic_")

					if is_directory_path(imagefilepath):
						is_dir = True
					else:
						imagefile = Path(imagefilepath)
						if imagefile.is_dir():
							is_dir = True
						else:
							imagepathok = True

			except Exception as e:
				if str(e) == "_cic_":
					return False
			finally:
				if imagepathok is True:
					self._imagepath = imagefile
					return True

		if is_dir is True:
			raise Exception("Image path '{}' points to a directory. Needs to be a file!")

	def set_device(self, devicepath: str = None) -> None:
		device_str = None

		if not string_is_empty(devicepath):
			self._devicepath = Path(devicepath)
		else:
			device_str = strip(
				input(
					"Type the path of device (e.g. /dev/sde) or partition (e.g. /dev/sde1) you want to backup:\n"
				)
			)

			if string_is_empty(device_str):
				raise Exception("Device-String is empty")

			devok = False

			for dev in self._devices:
				if string_equal_utf8(dev["dev"], device_str, False):
					devok = True

				if devok is False:
					if "partitions" in dev:
						for devpart in dev["partitions"]:
							if devpart["dev"] == device_str:
								devok = True
								break

				if devok is True:
					break

			if not devok:
				raise Exception("Device or partition '{}' not found".format(self._device_str))
			else:
				self._devicepath = Path(device_str)

	def start_dd(self, interactive: bool = False, ddbatchsize: str = None, finished_handler: Callable=None) -> int:
		retcode = None
		devpath = str(self._devicepath.absolute())
		imagepath = str(self._imagepath.absolute())

		param_if = "if={}".format(devpath.replace(" ", "\\ "))
		param_of = "of={}".format(imagepath.replace(" ", "\\ "))
		param_status = "status=progress"

		# todo: make configurable batch size
		if ddbatchsize is not None:
			param_bs = "bs={}".format(ddbatchsize)
		else:
			param_bs = "bs=1M"

		if interactive is True:
			yn = "y"
		else:
			print(ConsoleColor.colorline("Will execute \"{}\"".format(
				"sudo dd {} {} {} {}".format(param_if, param_of, param_status, param_bs)
			), ConsoleColors.OKGREEN))

			yn = singlecharinput(
				"Confirm the creation of image '{}' from device '{}' (y/n)!".format(
					imagepath, devpath
				), ConsoleColors.OKGREEN
			)

		if yn == "n":
			if interactive is True:
				print(ConsoleColor.colorline("Cancelled image creation on your wish", ConsoleColors.OKBLUE))
			return -1
		elif yn == "y":
			sudo = local["sudo"]
			dd = local["dd"]

			starttime = datetime.now()

			p = sudo[dd[param_if, param_of, param_status, param_bs]].popen(stderr=PIPE)
			line = ''
			# retcode = 0

			# Intention is not to get the first "\r" from dd-output
			# sleep(1)
			if interactive is True:
				print()

			target_image_sizehuman = self.get_target_image_sizehuman()
			target_image_sizebytes = self.get_target_image_sizebytes()

			if interactive is False:
				p._proc.communicate()
			else:
				while True:
					retcode = p.poll()
					if retcode is None:
						out = p.stderr.read(1).decode("utf-8", errors="replace")
						if out == '':
							break
						else:
							if out == '\r':
								line = strip(line)
								if not string_is_empty(line):
									dd_info = parse_dd_info(line)
									currenttime = datetime.now()
									deltatime = currenttime - starttime

									print(
										"{0:10}{1:4}{2:9}{3:3}{4:10}{5:4}{6:8}{7:3}{8}".format(
											bytes_to_unit(dd_info["size_b"], True, True, False),
											"of",
											target_image_sizehuman,
											"|",
											dd_info["time_h"],
											"of",
											humantime(
												predict_job_time(
													dd_info["time"],
													target_image_sizebytes,
													dd_info["size_b"]
												)
											),
											"|",
											"Total time: {}".format(humantime(deltatime.total_seconds()))
										),
										end="\r"
									)

								line = ''
							else:
								line = line + out
					else:
						break

			retcode = retcode if retcode is not None else p._proc.returncode

			if interactive is True:
				print()

				currenttime = datetime.now()
				deltatime = currenttime - starttime
				print(
					ConsoleColor.colorline(
						"Total time: {}".format(
							humantime(deltatime.total_seconds())
						), ConsoleColors.OKGREEN
					)
				)

				st = stat(imagepath)
				print(
					ConsoleColor.colorline(
						"Final image size: {}".format(
							bytes_to_unit(st.st_size, True, True, False)
						), ConsoleColors.OKGREEN
					)
				)
				if retcode == 0:
					print(ConsoleColor.colorline("Successfully created image!", ConsoleColors.OKGREEN))
				else:
					print(ConsoleColor.colorline("No Result from dd (image might be ok)!", ConsoleColors.WARNING))
			finished_handler(retcode, imagepath)
			return retcode
