"""
Exports the Job class.
"""

import argparse
import configparser
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from itertools import product
from os import path
from platform import uname
from typing import Sequence, Tuple


class Job(ABC):
	"""
	Run a simulation job (a range of simulations with some specified parameters)
	"""

	def __init__(self, description: str):
		"""
		Parse parameters from CLI and settings.ini
		:param str description: Description for help text
		"""
		# Parse CLI arguments
		parser = argparse.ArgumentParser(description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

		# Create dict of lists from argument string where several variables are separated by spaces, variable names and
		# their values are separated by =, and values are a comma-separated list
		parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
		self.args = parser.parse_args()

		# Parse ini file
		config = configparser.ConfigParser(converters={'list': lambda s: s.split(' ')})
		config.optionxform = str  # Use case-sensitive keys
		config.read('settings.ini')
		self.config = config

		# Assert that data file exists
		if not path.isfile(config['gcmc_vars']['equi_data']):
			raise RuntimeError("Missing equilibrated data file.")

		# Assert all required gcmc vars are accounted for
		for var in config.getlist('job', 'required_gcmc_vars'):
			if var not in config['gcmc_vars'] and var not in config['gcmc_dyn_vars']:
				raise RuntimeError("Missing value for GCMC variable '{}'".format(var))

		self.static_vars = dict(config['gcmc_vars'])
		# Get dict of dynamic vars
		self.gcmc_dyn_vars = {var: config.getlist('gcmc_dyn_vars', var) for var in config['gcmc_dyn_vars']}

		# Create Cartesian product of dynamic var values. Returns flat list of tuples (*vars)
		dyn_values_list = list(product(*self.gcmc_dyn_vars.values()))

		logging.info(datetime.now())
		logging.info(' '.join(uname()))
		logging.info("Got {} simulations".format(len(dyn_values_list)))

		self._spawn_simulations(dyn_values_list)

	@abstractmethod
	def _spawn_simulations(self, dyn_values_list: Sequence[Tuple]) -> None:
		"""
		Dispatch simulations
		:param dyn_values_list: List of tuples of values for the dynamic variables
		"""
		pass
