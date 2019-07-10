#!/usr/bin/env python3

"""
Samples a rough 4x4 mesh grid (16 points) in the 2D EPP-EPS parameter space.
No MPI; different points are simulated in parallel using Python multiprocessing.
"""

from multiprocessing import Pool
from itertools import product
from os import mkdir, chdir

from lammps import lammps

epp = [0.6, 1.0, 1.4, 2.0]
eps = [0.2, 0.6, 1.0, 1.4]

# Create cartesian product of two parameters. Returns list of tuples (epp, eps)
coordList = list(product(epp, eps))


def sample_coord(epp, eps):
	"""
	Simulate a system with the given parameters
	:param epp: epsilon
	:param eps:
	:return:
	"""
	# Create a subdirectory for every simulation
	subdir = 'grid_{}_{}'.format(epp, eps)
	mkdir(subdir)

	chdir(subdir)
	run_lammps_simulation(epp, eps)
	chdir('../')


def run_lammps_simulation(epp, eps):
	# Instantiate LAMMPS object
	lmp = lammps()

	lmp.command('variable epp equal {}'.format(epp))
	lmp.command('variable eps equal {}'.format(eps))

	# Run 'header' of equilibration input file
	lmp.file('../in.b_equi_header')

	# Run
	lmp.file('../in.b_equi_run')
	lmp.file('../in.b_gcmc_run')

	lmp.close()


if __name__ == '__main__':
	# Create pool of number of cores workers
	with Pool() as p:
		outputList = p.starmap(sample_coord, coordList)
