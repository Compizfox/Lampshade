"""
Exports the Simulation class.
"""

from datetime import datetime
from os import chdir, mkdir, path
from platform import uname
from subprocess import run


class Simulation:
	"""
	Run a vapour hydrated brush simulation in a standard manner. Handles creating subdirectories and cd'ing in and
	back out, passes equal-style variables.
	Wraps LAMMPS.
	"""

	def __init__(self, command: str, input_filename: str, log_filename: str, dry_run: bool = False,
	             verbose: bool = False, prefix: str = ""):
		"""
		:param str  command: Command to run to call LAMMPS.
		:param str  input_filename: Filename of the LAMMPS input file
		:param str  log_filename:   Filename of the log file to write to
		:param bool dry_run: Doesn't do anything productive if true.
		:param str  prefix:  String to prepend to all print() output.
		"""
		self.command = command
		self.dry_run = dry_run
		self.input_filename = input_filename
		self.log_filename = log_filename
		self.verbose = verbose
		self.prefix = prefix

	def _run_with_vars(self, input_filename: str, lmp_vars: dict = None) -> None:
		"""
		Run a LAMMPS simulation in a subprocess with variables.
		:param str  input_filename: Filename of the LAMMPS input file
		:param dict lmp_vars: Dictionary describing LAMMPS equal-style variables to set
		"""
		if lmp_vars is None:
			lmp_vars = {}

		with open(self.log_filename, 'w') as f:
			cmd = self.command + ' -in {} '.format(input_filename) + ''.join(
				['-var {} {} '.format(k, v) for k, v in lmp_vars.items()])
			if self.verbose:
				print("{} {}: Spawning LAMMPS:\n".format(self.prefix, datetime.now()) + cmd)
			run(cmd, universal_newlines=True, stdout=f, shell=True)

	def _run_in_subdir(self, subdir: str, lmp_vars: dict = None) -> None:
		"""
		Run a simulation in a subdirectory.
		:param str subdir:    Name of the subdirectory to run the simulation in
		:param dict lmp_vars: Dictionary describing LAMMPS equal-style variables to set
		"""
		if lmp_vars is None:
			lmp_vars = {}

		# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
		if not path.isdir(subdir):
			print("{} {}: Simulating {}...".format(self.prefix, datetime.now(), subdir))
			if not self.dry_run:
				mkdir(subdir)
				chdir(subdir)

				# Modify paths to files in parent directories
				lmp_vars['initial_data_file'] = '../' + lmp_vars['initial_data_file']
				input_filename = '../' + self.input_filename

				self._run_with_vars(input_filename, lmp_vars)
				chdir('../')
				print("{} {}: Finished {}.".format(self.prefix, datetime.now(), subdir))
		else:
			print("{} {}: Found existing subdir {}. Skipping.".format(self.prefix, datetime.now(), subdir))

	def run_gcmc(self, static_vars: dict = None, dyn_vars: dict = None) -> None:
		"""
		Simulate a system with the given parameters.
		:param dict static_vars: Dictionary describing static variables
		:param dict dyn_vars:    Dictionary describing dynamic variables
		"""
		if static_vars is None:
			static_vars = {}
		if dyn_vars is None:
			dyn_vars = {}

		if self.verbose:
			print(" ".join(uname()))

		subdir = 'grid' + ''.join(['_{}{:.4f}'.format(k, float(v)) for k, v in dyn_vars.items()])

		# Combine vars dicts
		static_vars.update(dyn_vars)

		self._run_in_subdir(subdir, static_vars)
