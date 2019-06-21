from plumbum import local
from typing import List, Dict
from fileutilslib.disklib.filetools import bytes_to_unit, FileSizes
from fileutilslib.misclib.helpertools import string_is_empty, strip, find_char_backwards


def predict_job_time(secs, target_sizebytes, current_sizebytes):
	return (target_sizebytes / current_sizebytes) * secs


def fdisk_size_to_bytesize(fdisksize: str) -> int:
	sfdisksize = strip(fdisksize)
	ffdisksize = None

	t = -1

	if sfdisksize.find("T") > -1:
		t = 0
	elif sfdisksize.find("G") > -1:
		t = 1
	elif sfdisksize.find("M") > -1:
		t = 2

	if t > -1:
		sfdisksize = sfdisksize[0:len(sfdisksize)-1].replace(",", ".")
		ffdisksize = float(sfdisksize)

	if t == 0:
		return int(ffdisksize * FileSizes.TB_BYTE_SIZE.value)
	elif t == 1:
		return int(ffdisksize * FileSizes.GB_BYTE_SIZE.value)
	elif t == 2:
		return int(ffdisksize * FileSizes.MB_BYTE_SIZE.value)
	else:
		return int(sfdisksize)


def fdiskdevicesize(devs_from_fdisk, device_name: str):
	if string_is_empty(device_name):
		return None

	device_name_l = device_name.lower()
	dev_size = None
	invalid_dev = False

	for dev in devs_from_fdisk:
		if "dev" in dev:
			if dev["dev"].lower() == device_name_l:
				if "size_b" in dev:
					dev_size = dev["size_b"]
				break
			if "partitions" in dev:
				for part in dev["partitions"]:
					if "dev" in part and part["dev"].lower() == device_name_l:
						if "size_b" in part:
							dev_size = part["size_b"]
						else:
							invalid_dev = True
						break
			if dev_size is not None or invalid_dev is True:
				break

	return dev_size


def fdisklist(dbgout: bool=True) -> List[str]:
	sudo = local["sudo"]
	fdisk = local["fdisk"]
	retcode, stdout, stderr = sudo[fdisk["-l"]].run(retcode=None)

	if retcode != 0:
		raise Exception(stderr)

	devs = []

	startedpartitions = False
	isboottype = False

	for line in stdout.splitlines():
		line = line.strip()

		if startedpartitions is True:
			if len(line) == 0:
				startedpartitions = False
			else:
				pd = parse_partition_line(line, isboottype)
				if dbgout:
					print("\t" + pd["dev"] + " - " + pd["size_h"] + " - " + pd["type"])
				dev["partitions"].append(pd)
		else:
			if line.startswith("Disk /dev/"):
				sizeinfo = parse_device_sizeinfo(line)
				devstr = line[5:line.find(":")]
				dev = {
					"dev": devstr,
					"isntfs": False,
					"partitions": [],
					"size_b": sizeinfo["size_b"],
					"size_h": sizeinfo["size_h"]
				}
				devs.append(dev)
				if dbgout:
					print("=========================================")
					print(line)
			if line.startswith("Disklabel"):
				if dbgout:
					print(line)
			if line.startswith("Disk identifier"):
				if dbgout:
					print(line)

			if line.startswith("Device "):
				isboottype = False
				if line.find("Boot") > -1:
					isboottype = True

				startedpartitions = True

			if line.find("HPFS/NTFS/exFAT") > -1:
				devs[len(devs)-1]["isntfs"] = True
				if dbgout:
					print("NTFS")
	return devs


def parse_device_sizeinfo(line: str) -> Dict:
	if string_is_empty(line):
		return None
	p = line.find("bytes")
	c = find_char_backwards(line, ",", len(line) - p)
	fsize = int(strip(line[(p - c):p]))
	return {
		"size_b": fsize,
		"size_h": bytes_to_unit(fsize, True)
	}


def parse_partition_line(line: str, isboottype: bool) -> Dict:

	if string_is_empty(line):
		return None

	columns = {}
	columncount = 7 if isboottype else 6
	startedgap = False
	lastcolumn = False
	columncollect = ""
	collect = False
	cc = 0

	for c in line:
		if c == ' ' and lastcolumn is False:
			if startedgap is False:
				collect = False
				if isboottype:
					if cc == 0 or cc == 4 or cc == 6:
						collect = True
				else:
					if cc == 0 or cc == 4 or cc == 5:
						collect = True
				if collect is True:
					if cc == 0:
						columns["dev"] = columncollect
					elif cc == 4:
						partbytes = fdisk_size_to_bytesize(columncollect)
						columns["size_b"] = partbytes
						columns["size_h"] = bytes_to_unit(partbytes, True)

				startedgap = True
				cc += 1
				columncollect = ""
		else:
			if cc == columncount - 1:
				lastcolumn = True
			if startedgap is True:
				startedgap = False
			columncollect += c
	columns["type"] = columncollect
	return columns
