#!/usr/bin/env python3

"""
Runs a range of simulation jobs with arbitrarily varied parameters.
No script-level MPI; different jobs are simulated in parallel using Python multiprocessing.

Maximum number of cores, paths to LAMMPS and mpirun and extra arguments to those are set in settings.ini.

Runs a (single, common) equilibration if equilibrated data file is not found with n-rank MPI where n is the number of
cores in the system.

Variables for the equilibration run must be set in settings.ini. Variables for the GCMC run can be set either in
settings.ini (static), or passed through the -var/--variable command-line argument, in which case an array of values
can be specified which will be run in parallel.

Fills up 'spare' cores with MPI parallelisation.
"""

import argparse
import configparser
from itertools import product
from math import floor
from multiprocessing import Pool, current_process
from os import path
from typing import Optional

from Simulation import Simulation


# We use a function with a global var here over a closure in __main__ because non-module-level functions are not
# callable by Pool.starmap for some reason
def start_sim(*vars_values: float) -> None:
	"""
	Start the simulation by creating a Simulation and running it.
	:param float *vars_values: Custom variable values
	"""
	static_vars = dict(config.items('gcmc_vars'))

	# Reconstruct dynamic vars dict
	dyn_vars = dict(zip(args.variable.keys(), vars_values))

	sim = Simulation(args.lammps_command, args.dry_run, current_process().name)
	sim.run_gcmc(static_vars, dyn_vars)


def init_pool(args_dict: dict, config_dict: dict) -> None:
	"""
	Initialise workers with arguments dict and config dict as global args.
	:param dict args_dict: Arguments
	:param dict config_dict: Config
	"""
	global args, config
	args = args_dict
	config = config_dict


def build_lammps_command(lammps_path: str, lammps_arguments: str, mpi_path: Optional[str], mpi_arguments: Optional[str],
                         mpi_ranks: Optional[int]) -> str:
	"""
	Build LAMMPS command from paths and arguments, optionally with MPI.
	:param str lammps_path:      Path to LAMMPS
	:param str lammps_arguments: Arguments to LAMMPS
	:param str mpi_path:         Path to mpirun (optional)
	:param str mpi_arguments:    Arguments to mpirun (mandatory if mpi_path is given)
	:param int mpi_ranks:        Number of MPI ranks to use (mandatory if mpi_path is given)
	:return: String containing the assembled LAMMPS command
	"""
	if mpi_path is not None:
		return ' '.join([mpi_path, mpi_arguments, '-n', str(mpi_ranks), lammps_path, lammps_arguments])
	else:
		return ' '.join([lammps_path, lammps_arguments])


if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Create dict of lists from argument string where several variables are separated by spaces, variable names and
	# their values are separated by =, and values are a comma-separated list
	parser.add_argument("-var", "--variable", default={}, type=lambda s:
	                    {k: [float(i) for i in v.split(',')] for k, v in [var.split('=') for var in s.split(' ')]},
	                    # ^ *Sometimes my genius is... it's almost frightening.*
	                    help="Arbitrary equal-style variable(s) to set. Can be arrays, with values separated by "
	                         "commas. In this case, a simulation will be run for every combination of values."
	                         "Multiple variables should be separated by spaces. Values should be floats. Example: -var "
	                         "mu=1.0,2.0 cps=1.5,2.0",
	                    metavar="VAR=VALUE")
	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	args = parser.parse_args()

	# Parse ini file
	config = configparser.ConfigParser(converters={'list': lambda s: s.split(' ')})
	config.optionxform = str  # Use case-sensitive keys
	config.read('settings.ini')

	cpu_count = int(config['system']['num_cores'])
	lammps_path = config['lammps']['LAMMPS_path']
	lammps_arguments = config['lammps'].get('LAMMPS_arguments', '')
	mpi_path = config['lammps'].get('MPI_path')
	mpi_arguments = config['lammps'].get('MPI_arguments', '')

	# Run equilibration if equilibrated data file is not found
	if not path.isfile('data.equi'):
		# Gather equi vars from config
		equi_vars = dict(config.items('equi_vars'))

		# Assert all required equi vars are accounted for
		for var in config.getlist('job', 'required_equi_vars'):
			if var not in equi_vars:
				raise RuntimeError("Missing value for equilibration variable '{}'".format(var))

		lammps_command = build_lammps_command(lammps_path, lammps_arguments, mpi_path, mpi_arguments, cpu_count)
		sim = Simulation(lammps_command, args.dry_run)
		sim.run_equi(equi_vars)

	# Assert all required gcmc vars are accounted for
	for var in config.getlist('job', 'required_gcmc_vars'):
		if var not in config['gcmc_vars'] and var not in args.variable.keys():
			raise RuntimeError("Missing value for GCMC variable '{}'".format(var))

	# Create Cartesian product of dynamic var values. Returns flat list of tuples (*vars)
	dyn_vars_list = list(product(*args.variable.values()))

	print("Got {} jobs, distributed over {} workers:".format(len(dyn_vars_list), cpu_count))
	print(*dyn_vars_list, sep="\n")

	# Calculate number of 'spare' cpu cores for MPI parallelisation
	mpi_ranks = floor(cpu_count / len(dyn_vars_list))
	if mpi_ranks == 0: mpi_ranks = 1
	args.lammps_command = build_lammps_command(lammps_path, lammps_arguments, mpi_path, mpi_arguments, mpi_ranks)

	# Create pool of number of cores workers
	with Pool(cpu_count, initializer=init_pool, initargs=(args, config)) as p:
		p.starmap(start_sim, dyn_vars_list)
