#!/usr/bin/env python3

"""
Run a simulation job (a range of simulations with some arbitrary specified parameters) on a SLURM-enabled system.

Simulations are submitted to SLURM using an ephemeral jobscript.

Specify the sbatch command including arguments in settings.ini (slurm_sbatch_args)

Variables for the simulation run must be set in settings.ini under [static_vars] and [dyn_vars]. The first
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
			dyn_vars = dict(zip(self.dyn_vars.keys(), dyn_values))

			# Build jobscript
			jobscript = "#!/bin/sh\n\n"
			jobscript += f"/usr/bin/env python3 ../run_simulation.py '{json.dumps(self.lammps_command)}' " \
			             f"'{json.dumps(self.input_file)}' '{json.dumps(self.log_file)}' " \
			             f"'{json.dumps(self.args.dry_run)}' '{json.dumps(self.static_vars)}' '{json.dumps(dyn_vars)}'"

			run(self.slurm_sbatch_cmd, input=jobscript, universal_newlines=True, shell=True)

			logging.info(f"Submitted SLURM job with {self.slurm_sbatch_cmd}:\n"
			             f"LAMMPS command: {self.lammps_command}\n"
			             f"Static vars: {self.static_vars}\n"
			             f"Dynamic vars: {dyn_vars}\n")


job = SlurmJob(description=__doc__)
