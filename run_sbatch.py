#!/usr/bin/env python3

"""
Runs a range of simulation jobs with arbitrarily varied parameters.

This version of the grid script does not use the LAMMPS Python library, multiprocessing, or MPI. Rather, it is called in
a sbatch job script and spawns MPI-enabled LAMMPS simulations using srun.

Paths to LAMMPS and srun and extra arguments to those are set in settings.ini.

Variables for the simulation run must be set in settings.ini.
"""

import configparser
from itertools import product
from os import environ

from Simulation import Simulation

if __name__ == '__main__':
	# Parse ini file
	config = configparser.ConfigParser(converters={'list': lambda s: s.split(' ')})
	config.optionxform = str  # Use case-sensitive keys
	config.read('settings_sbatch.ini')

	lammps_path = config['lammps']['LAMMPS_path']
	lammps_arguments = config['lammps'].get('LAMMPS_arguments', '')
	mpi_path = config['lammps'].get('MPI_path')
	mpi_arguments = config['lammps'].get('MPI_arguments', '')

	# Assert all required gcmc vars are accounted for
	for var in config.getlist('job', 'required_gcmc_vars'):
		if var not in config['gcmc_vars'] and var not in config['gcmc_dyn_vars']:
			raise RuntimeError("Missing value for GCMC variable '{}'".format(var))

	# Get dict of dynamic vars
	gcmc_dyn_vars = {var: config.getlist('gcmc_dyn_vars', var) for var in config['gcmc_dyn_vars']}

	# Create Cartesian product of dynamic var values. Returns flat list of tuples (*vars)
	dyn_values_list = list(product(*gcmc_dyn_vars.values()))

	# Read from SLURM_ARRAY_TASK_ID environment variable which combination of dynamic var values to run and
	# reconstruct dynamic vars dict
	dyn_vars = dict(zip(gcmc_dyn_vars.keys(), dyn_values_list[int(environ['SLURM_ARRAY_TASK_ID'])]))

	# Run simulation
	static_vars = dict(config.items('gcmc_vars'))
	lammps_command = ' '.join([mpi_path, mpi_arguments, lammps_path, lammps_arguments])

	sim = Simulation(lammps_command)
	sim.run_gcmc(static_vars, dyn_vars)
