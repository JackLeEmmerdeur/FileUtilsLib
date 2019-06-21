# from distutils.core import setup
# from sys import platform
from setuptools import setup

ir = [
	'click >= 7.0',
	'plumbum >= 1.6.6',
	'six >= 1.11.0'
]

setup(
	name='FileUtilsLib',
	version='0.0.1',
	description='Helper code for file operations (fdisk, dd, general)',
	long_description='Library containing file helper code (fdisk, dd, general) for Application BackTheFooUp and EasyDD',
	author='Daniel Hilker',
	author_email='daniel@buccaneersdan.de',
	url='https://github.com/JackLeEmmerdeur/FileUtilsLib',
	install_requires=ir,
	download_url='https://github.com/JackLeEmmerdeur/FileUtilsLib/tarball/0.0.1',
	keywords=['file', 'dd', 'fdisk', 'general-helpers'],
	packages=[
		'fileutilslib',
		'fileutilslib.disklib',
		'fileutilslib.misclib',
	],
	classifiers=[
		'Development Status :: 0.0.1 - Alpha',
		'Environment :: Console',
		'Intended Audience :: Developers',
		'License :: Freeware',
		'Programming Language :: Python :: 3'
	]
)
