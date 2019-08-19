#!/usr/bin/env python3

"""
Runs one simulation with the given parameters.

Call with double dash to specify negative values for the required positional arguments, for example:
run_grid.py -- 1.0 1.0 -3.5,-3.0
"""

import argparse

from Simulation import Simulation

if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("epp", type=float, help="Epp value")
	parser.add_argument("eps", type=float, help="Eps value")
	parser.add_argument("p", type=float, help="Pressure value")
	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp_daily',
						help="Path to the LAMMPS binary. May be a command, like \"mpirun lmp\"")
	parser.add_argument("-r", "--run", type=int, default=9000000, help="Run GCMC for n timesteps")
	args = parser.parse_args()

	parameters = (args.epp, args.eps, args.p)
	print(parameters)

	sim = Simulation(args.lammps_path, args.run, args.dry_run)
	sim.sample_coord(*parameters)
