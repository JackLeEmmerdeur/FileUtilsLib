from datetime import datetime


class Bencher:
	_d1 = None
	_d2 = None

	def __init__(self):
		pass

	def _assert_bench_ran(self):
		if self._d1 is None or self._d2 is None:
			raise Exception("startbench() or endbench() hasn't been called")

	def startbench(self):
		self._d1 = datetime.now()

	def endbench(self):
		self._d2 = datetime.now()

	def get_result(self):
		self._assert_bench_ran()
		return self._d2 - self._d1

	def get_result_seconds(self):
		return (self._d2 - self._d1).total_seconds()