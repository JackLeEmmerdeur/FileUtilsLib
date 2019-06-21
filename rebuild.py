import click
from plumbum import local
from plumbum import FG
from sys import platform
from os import unlink
from os.path import isdir
import glob
from itertools import chain
import struct
# from six import string_types
import traceback
from os import system, path

sudo = local["sudo"]

python_bitness = 8 * struct.calcsize("P")


def install_wheel(pip, version):
	print("")
	print("Installing available wheels")
	sudo = local["sudo"]
	wheels = glob.glob('dist/*.whl')

	for wheel in wheels:
		print("    Wheel '{}'".format(wheel))
		rcode, stdout, stderr = sudo[pip["install", wheel]].run(retcode=None)
		if "mysql_config not found" in stdout:
			print("Installing ConfigParser")
			rcode, stdout, stderr = sudo[pip["install", "ConfigParser"]].run(retcode=None)
			print(rcode)
			print(stdout)
			print(stderr)

			if version == 2:
				rcode, stdout, stderr = sudo[pip["install", "mysql-python"]].run(retcode=None)
			elif version == 3:
				rcode, stdout, stderr = sudo[pip["install", "mysqlclient"]].run(retcode=None)
			print(rcode)
			print(stdout)
			print(stderr)
			aptget = local["apt-get"]
			rcode, stdout, stderr = sudo[sudo[aptget["install libmysqlclient-dev"]]].run(retcode=None)
		elif "Exception" in stdout:
			stderr = stdout
		if not string_is_empty(stderr):
			if not "/.cache/" in stderr:
				raise (Exception("Could not install wheel: {}".format(stderr)))


def post_install(python, version):
	posinstall_all = glob.glob('requirements/all/postinstall.py'.format(version))
	postinstall_bitless = glob.glob('requirements/{}/postinstall.py'.format(version))
	postinstall_with_bitness = glob.glob('requirements/{}/{}/postinstall.py'.format(version, python_bitness))
	requirements = chain(posinstall_all, postinstall_bitless, postinstall_with_bitness)
	pythoncmd = python.executable
	import subprocess
	for f in requirements:
		cmd = pythoncmd + " " + f + " " + pythoncmd + " " + path.dirname(pythoncmd) + "/Scripts"
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		out, err = p.communicate()
		if out is not None and len(out) > 0:
			result = out.split('\n')
			for lin in result:
				if not lin.startswith('#'):
					print(lin)
		if err is not None:
			print(err)


def get_pip_and_python(version):
	print("")
	print("Finding Python and Pip Executables for version {}".format(version))
	if version == 2:
		pip = local["pip2"]
		python = local["python2"]
	elif version == 3:
		pip = local["pip3"]
		python = local["python3"]
	elif version == 36:
		pip = local["pip3.6"]
		python = local["python3.6"]
	else:
		raise Exception("No valid python version")
	print("    Python={}".format(python))
	print("    Pip={}".format(pip))
	return pip, python


def install_extra_requirements(pip, version):
	print("")
	print("Installing extra requirements")
	if isdir("requirements"):
		# version 2 and 3, current bitness
		requirements_all = glob.glob('requirements/all/{}/*'.format(python_bitness))

		# version 2 and 3, any bitness
		requirements_all_any = glob.glob('requirements/all/any/*'.format(python_bitness))

		# current version, current bitness
		requirements_version = glob.glob('requirements/{}/{}/*'.format(version, python_bitness))

		requirements_all = chain(requirements_all, requirements_all_any, requirements_version)

		for requirement in requirements_all:
			print("    Requirement '{}'".format(requirement))
			rcode, stdout, stderr = pip["install", "--no-index", '--find-links="."', requirement].run()
			if not string_is_empty(stderr):
				raise (Exception("Could not install extra requirement: {}".format(stderr)))


def remove_package(pip, version, package_name):
	installed = is_pip_package_installed(pip, version, package_name)
	print("")
	sudo = local["sudo"]
	if installed:
		print("Removing package '{}' via Pip".format(package_name))
		sudo[pip["uninstall", package_name]] & FG
	if isdir("dist"):
		print("")
		print("Removing Wheel-Files in dist".format(package_name))
		files = glob.glob('dist/*')
		rm = local["rm"]
		for f in files:
			print("    Wheel-File '{}'".format(f))
			sudo[rm[f]]
			# unlink(f)


def create_wheel(python, pip):
	print("")
	# from setup import ir
	# print(ir)
	rcode, stdout, stderr = sudo[python["setup.py", "bdist_wheel"]].run(retcode=None)
	is_wheel_installed = False
	if not string_is_empty(stderr):
		if "invalid command 'bdist_wheel'" in stderr:
			print("Pythons Wheel-Package not installed. Installing.")
			pip["install", "wheel"] & FG
			is_wheel_installed = True
		elif "Normalizing" not in stderr:
			raise (Exception(stderr))
	if is_wheel_installed:
		print("Creating Wheel-File")
		rcode, stdout, stderr = python["setup.py", "bdist_wheel"].run(retcode=None)
		if not string_is_empty(stderr):
			raise (Exception("Could not create wheel: {}".format(stderr)))


def is_pip_package_installed(pip, version, package_name):
	print("")
	print("Checking if Package '{}' is installed".format(package_name))

	(rcode, stdout, stderr) = pip["list"].run(retcode=None)

	if not string_is_empty(stderr):
		stderrl = stderr.lower()
		if "deprecation" in stderrl and "--format" in stderrl:
			(rcode, stdout, stderr) = pip["list", "--format=legacy"].run(retcode=None)

	if not string_is_empty(stderr):
		raise Exception("Pip failed: {}".format(stderr if version == 2 else stderr.replace("python", "python3")))

	if rcode != 0:
		raise Exception("Pip doesn't seem to be installed")

	installed = False

	if not string_is_empty(stdout):
		for l in stdout.splitlines():
			if package_name in l:
				installed = True

	print("    {}".format("Yes" if installed else "No"))
	return installed


def string_is_empty(thetext):
	return not (thetext and (hasattr(thetext, "strip") and thetext.strip()))


@click.command()
@click.option("--version", default=2, help="2/3/3.6: Python-version")
@click.option("--package", help="The name of the package defined in setup.py without version number")
@click.option('--multiproc', type=click.UNPROCESSED)
@click.option('--client', type=click.UNPROCESSED)
@click.option('--qt-support', type=click.UNPROCESSED)
@click.option('--client', type=click.UNPROCESSED)
@click.option('--port', type=click.UNPROCESSED)
@click.option('--file', type=click.UNPROCESSED)
def test(version, package, multiproc, client, qt_support, port, file):
	if string_is_empty(package):
		raise (Exception("Package Command-line Option empty"))

	try:

		pip, python = get_pip_and_python(version)

		remove_package(pip, version, package)

		if "win" in platform:
			install_extra_requirements(pip, version)

		# rcode, stdout, stderr = pip["install", "--upgrade", "setuptools"].run(retcode=None)
		# if rcode != 0:
		# 	raise Exception(stdout + "\n" + stderr)

		create_wheel(python, pip)

		install_wheel(pip, version)

		post_install(python, version)

	except Exception as exc_proc:
		if hasattr(exc_proc, 'stderr'):
			raise Exception(exc_proc.stderr)
		else:
			raise exc_proc


if __name__ == '__main__':
	try:
		test()
	except Exception as e:
		print(traceback.print_exc())
		print("Will not install underware!")
