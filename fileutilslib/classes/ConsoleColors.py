from enum import Enum


class ConsoleColors(Enum):
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	NONE = '_'


class ConsoleColor:
	@staticmethod
	def colorline(line: str, color: ConsoleColors):
		return ("{}" + line.replace("{}", "") + "{}").format(color.value, ConsoleColors.ENDC.value)
