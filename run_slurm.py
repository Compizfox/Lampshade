#!/usr/bin/env python3

"""
Run a simulation job (a range of simulations with some arbitrary specified parameters) on a SLURM-enabled system.

Simulations are submitted to SLURM using an ephemeral jobscript.

Specify the sbatch command including arguments in settings.ini (slurm_sbatch_args)

Variables for the simulation run must be set in settings.ini under [gcmc_vars] and [gcmc_dyn_vars]. The first
section contains static variables, whereas the latter can contain variables assigned an array of values which will be
run in parallel.
"""

import json
import logging
from subprocess import run
from typing import Sequence, Tuple

from Job import Job


class SlurmJob(Job):
	"""
	Extends Job and implements _spawn_simulations() to submit SLURM jobs using sbatch.
	"""

	def _spawn_simulations(self, dyn_values_list: Sequence[Tuple]) -> None:
		for dyn_values in dyn_values_list:
			# Reconstruct dynamic vars dict
			dyn_vars = dict(zip(self.gcmc_dyn_vars.keys(), dyn_values))

			lammps_command = ' '.join([
				self.config['lammps'].get('MPI_path'),
				self.config['lammps'].get('MPI_arguments', ''),
				self.config['lammps']['LAMMPS_path'],
				self.config['lammps'].get('LAMMPS_arguments', '')
			])

			# Build jobscript
			jobscript = "#!/bin/sh\n\n"
			jobscript += f"/usr/bin/env python3 ../run_simulation.py '{json.dumps(lammps_command)}' " \
			             f"'{json.dumps(self.args.dry_run)}' '{json.dumps(self.static_vars)}' '{json.dumps(dyn_vars)}'"

			run(self.config['job']['slurm_sbatch_args'], input=jobscript, universal_newlines=True, shell=True)

			logging.info(f"Submitted SLURM job:\n"
			             f"LAMMPS command: {lammps_command}\n"
			             f"Static vars: {self.static_vars}\n"
			             f"Dynamic vars: {dyn_vars}\n")


logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("wrapper.log"), logging.StreamHandler()])

job = SlurmJob(description=__doc__)
