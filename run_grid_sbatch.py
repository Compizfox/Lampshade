#!/usr/bin/env python3

"""
Samples a rough 4x4 mesh grid (16 points) in the 2D EPP-EPS parameter space.

This version of the grid script does not use the LAMMPS Python library, multiprocessing, or MPI. Rather, it is called in
a sbatch job script and spawns MPI-enabled LAMMPS simulations using srun.
"""

from itertools import product
from os import mkdir, chdir, path, environ
from subprocess import run, DEVNULL
from io import StringIO

EPP = [0.6, 1.0, 1.4, 2.0]
EPS = [0.2, 0.6, 1.0, 1.4]


def sample_coord(epp: float, eps: float) -> None:
	"""
	Simulate a system with the given parameters
	:param epp: self-interation of polymer
	:param eps: interaction of polymer with solvent
	:return:
	"""
	# Build LAMMPS input script
	buf = StringIO()
	buf.write('variable epp equal {}\n'.format(epp))
	buf.write('variable eps equal {}\n'.format(eps))
	# 'header' of equilibration input file
	with open('in.b_equi_header') as f:
		buf.write(f.read())
	# Equilibration
	with open('in.b_equi_run') as f:
		buf.write(f.read())
	# Initial GCMC run (from scratch, 9M timesteps)
	with open('in.b_gcmc_rcb') as f:
		buf.write(f.read())
	buf.write('run 9000000\n')
	buf.write('write_data data.gcmc\n')

	subdir = 'grid_{}_{}'.format(epp, eps)
	run_in_subdir(buf.getvalue(), subdir)


def run_in_subdir(input_script: str, subdir: str) -> None:
	"""
	Runs a simulation in a subdirectory.
	:param input_script: String containing the LAMMPS input script.
	:param subdir: String containing the subdirectory to run the simulation in.
	"""
	# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
	if not path.isdir(subdir):
		mkdir(subdir)
		chdir(subdir)
		run('srun lmp', input=input_script, universal_newlines=True, shell=True)
		chdir('../')


if __name__ == '__main__':
	# Create cartesian product of two parameters. Returns list of tuples (epp, eps)
	coordList = list(product(EPP, EPS))

	# Read from SLURM_ARRAY_TASK_ID environment variable which pair to run
	coord = coordList[int(environ['SLURM_ARRAY_TASK_ID'])]
	sample_coord(*coord)
