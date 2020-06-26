"""
Exports the Job class.
"""

import argparse
import configparser
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from itertools import product
from os import path, chdir
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
		parser.add_argument("subdir", help="Subdir to use for this job")
		self.args = parser.parse_args()

		# Assert that subdir exists and chdir in it
		if not path.isdir(self.args.subdir):
			raise RuntimeError("Subdir '{}' does not exist.".format(self.args.subdir))
		chdir(self.args.subdir)

		# Setup logging
		logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("wrapper.log"), logging.StreamHandler()])

		# Setup parser
		config = configparser.ConfigParser(converters={'list': lambda s: s.split(' ')})
		config.optionxform = str  # Use case-sensitive keys

		# Assert that settings file exist and parse it
		if not path.isfile('settings.ini'):
			raise RuntimeError("settings.ini does not exist in specified subdir {}".format(self.args.subdir))
		config.read('settings.ini')

		# Assert that input file exists
		input_file = config['job']['input_file']
		if not path.isfile(input_file):
			raise RuntimeError("Missing input file: {}".format(input_file))

		# Assert that data file exists
		data_file = config['gcmc_vars']['equi_data']
		if not path.isfile(data_file):
			raise RuntimeError("Missing equilibrated data file: {}".format(data_file))

		# Assert all required gcmc vars are accounted for
		for var in config.getlist('job', 'required_gcmc_vars'):
			if var not in config['gcmc_vars'] and var not in config['gcmc_dyn_vars']:
				raise RuntimeError("Missing value for GCMC variable '{}'".format(var))

		self.static_vars = dict(config['gcmc_vars'])
		# Get dict of dynamic vars
		self.gcmc_dyn_vars = {var: config.getlist('gcmc_dyn_vars', var) for var in config['gcmc_dyn_vars']}
		self.lammps_command = ' '.join([
			config['lammps'].get('MPI_path'),
			config['lammps'].get('MPI_arguments', ''),
			config['lammps']['LAMMPS_path'],
			config['lammps'].get('LAMMPS_arguments', '')
		])
		self.slurm_sbatch_cmd = config['job']['slurm_sbatch_args']
		self.input_file = input_file
		self.log_file = config['job']['log_file']

		# Create Cartesian product of dynamic var values. Returns flat list of tuples (*vars)
		dyn_values_list = list(product(*self.gcmc_dyn_vars.values()))

		logging.info(datetime.now())
		logging.info("Got {} simulations".format(len(dyn_values_list)))

		self._spawn_simulations(dyn_values_list)

	@abstractmethod
	def _spawn_simulations(self, dyn_values_list: Sequence[Tuple]) -> None:
		"""
		Dispatch simulations
		:param dyn_values_list: List of tuples of values for the dynamic variables
		"""
		pass
