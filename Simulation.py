"""
Exports the Simulation class.
"""

from os import mkdir, chdir, path
from subprocess import run
from io import StringIO
from datetime import datetime


class Simulation:
	"""
	Runs a vapour hydrated brush simulation in a standard manner. Wraps LAMMPS.
	"""
	def __init__(self, command: str, run: int, dry_run: bool = False, prefix: str = ""):
		"""
		:param command: Command to run to call LAMMPS.
		:param run: Number of timesteps to simulate for.
		:param dry_run: Doesn't do anything productive if true.
		:param prefix: String to prepend to all print() output.
		"""
		self.command = command
		self.run = run
		self.dry_run = dry_run
		self.prefix = prefix

	def sample_coord(self, epp: float, eps: float, p: float) -> None:
		"""
		Simulate a system with the given parameters
		:param epp: Self-interation of polymer
		:param eps: Interaction of polymer with solvent
		:param p: Pressure of the solvent
		:return:
		"""
		# Build LAMMPS input script
		buf = StringIO()
		buf.write('variable epp equal {:.2f}\n'.format(epp))
		buf.write('variable eps equal {:.2f}\n'.format(eps))
		buf.write('variable p equal {:.4f}\n'.format(p))
		# 'header' of equilibration input file
		with open('in.b_equi_header') as f:
			buf.write(f.read())
		# Equilibration
		with open('in.b_equi_run') as f:
			buf.write(f.read())
		# GCMC run
		with open('in.b_gcmc_rcb') as f:
			buf.write(f.read())
		buf.write('run {}\n'.format(self.run))
		buf.write('write_data data.gcmc\n')

		subdir = 'grid_{:.2f}_{:.2f}_{:.4f}'.format(epp, eps, p)
		self.run_in_subdir(buf.getvalue(), subdir)

	def run_in_subdir(self, input_script: str, subdir: str) -> None:
		"""
		Runs a simulation in a subdirectory.
		:param input_script: String containing the LAMMPS input script.
		:param subdir: String containing the subdirectory to run the simulation in.
		"""
		# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
		if not path.isdir(subdir):
			print("{} {}: Simulating {}...".format(self.prefix, datetime.now(), subdir))
			if not self.dry_run:
				mkdir(subdir)
				chdir(subdir)
				with open('log.{}'.format(subdir), 'w') as f:
					run(self.command, input=input_script, universal_newlines=True, stdout=f, shell=True)
				chdir('../')
				print("{} {}: Finished {}.".format(self.prefix, datetime.now(), subdir))
		else:
			print("{} {}: Found existing subdir {}. Skipping.".format(self.prefix, datetime.now(), subdir))
