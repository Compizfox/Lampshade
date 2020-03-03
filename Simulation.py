"""
Exports the Simulation class.
"""

from os import mkdir, chdir, path
from subprocess import run
from datetime import datetime


class Simulation:
	"""
	Run a vapour hydrated brush simulation in a standard manner. Wraps LAMMPS.
	"""

	def __init__(self, command: str, dry_run: bool = False, prefix: str = ""):
		"""
		:param str  command: Command to run to call LAMMPS.
		:param bool dry_run: Doesn't do anything productive if true.
		:param str  prefix:  String to prepend to all print() output.
		"""
		self.command = command
		self.dry_run = dry_run
		self.prefix = prefix

	def _run_with_vars(self, input_filename: str, log_filename: str, vars: dict = {}) -> None:
		"""
		Run a LAMMPS simulation in a subprocess with variables.
		:param str input_filename: Filename of the LAMMPS input file
		:param str log_filename:   Filename of the log file to write to
		:param dict vars:          Dictionary describing LAMMPS equal-style variables to set
		"""
		with open(log_filename, 'w') as f:
			run(self.command + ' -in {} '.format(input_filename) + ''.join(
				['-var {} {} '.format(k, v) for k, v in vars.items()]),
			    universal_newlines=True, stdout=f, shell=True)

	def _run_in_subdir(self, subdir: str, vars: dict = {}) -> None:
		"""
		Run a simulation in a subdirectory.
		:param str subdir: Subdirectory to run the simulation in
		:param dict vars:  Dictionary describing LAMMPS equal-style variables to set
		"""
		# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
		if not path.isdir(subdir):
			print("{} {}: Simulating {}...".format(self.prefix, datetime.now(), subdir))
			if not self.dry_run:
				mkdir(subdir)
				chdir(subdir)
				self._run_with_vars('../gcmc.in', 'gcmc.log', vars)
				chdir('../')
				print("{} {}: Finished {}.".format(self.prefix, datetime.now(), subdir))
		else:
			print("{} {}: Found existing subdir {}. Skipping.".format(self.prefix, datetime.now(), subdir))

	def run_gcmc(self, static_vars: dict = {}, dyn_vars: dict = {}) -> None:
		"""
		Simulate a system with the given parameters.
		:param dict vars: Dictionary describing LAMMPS equal-style variables to set
		"""
		subdir = 'grid' + ''.join(['_{}{:.4f}'.format(k, float(v)) for k, v in dyn_vars.items()])

		# Combine vars dicts
		static_vars.update(dyn_vars)

		self._run_in_subdir(subdir, static_vars)

	def run_equi(self, vars: dict = {}) -> None:
		"""
		Run equilibration.
		:param dict vars: Dictionary describing LAMMPS equal-style variables to set
		"""
		print("{}: Equilibrating...".format(datetime.now()))
		if not self.dry_run:
			self._run_with_vars('equi.in', 'equi.log', vars)
			print("{}: Finished equilibration.".format(datetime.now()))
