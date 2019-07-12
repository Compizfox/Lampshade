#!/usr/bin/env python3

"""
Refines grid using pairwise recursive bisectioning (RCB) sampling
"""

from multiprocessing import Pool
from os import mkdir, chdir, path
from typing import Tuple, List

from lammps import lammps
import numpy as np

from RegimeClassifier import RegimeClassifier

RCB_THRESHOLD = 0.1

# Boundary between regimes to probe
REGIMES = (2, 1)

# List of 2-tuples of 2-tuples, representing initial outer bound coords
pairs: List[Tuple[Tuple[float, float], Tuple[float, float]]] = [
	((1.0, 1.4), (1.4, 1.4)),
	((1.0, 1.4), (1.4, 1.0)),
	((1.0, 1.4), (1.0, 1.0)),
	((0.6, 1.0), (1.0, 1.0)),
	((0.6, 1.0), (0.6, 0.6)),
]


def sample_coord(lmp, epp: float, eps: float) -> int:
	"""
	Simulate a system with the given parameters and analyse the results to return a regime classification.
	:param lmp: LAMMPS instance
	:param epp: self-interation of polymer
	:param eps: interaction of polymer with solvent
	:return:
	"""
	# Create a subdirectory for every simulation. Skip simulation entirely if dir already exists
	subdir = 'rcb_{}_{}'.format(epp, eps)
	if not path.isdir(subdir):
		mkdir(subdir)

		chdir(subdir)
		lmp.command('variable epp equal {}'.format(epp))
		lmp.command('variable eps equal {}'.format(eps))
		lmp.file('../in.b_gcmc_run')
		chdir('../')

	rc = RegimeClassifier(subdir)
	return rc.get_classification()


def recursive_bisect(lmp, l: Tuple[float, float], r: Tuple[float, float]):
	"""
	Returns the middlepoint between two coords
	:param lmp: LAMMPS instance
	:param l:   Left coord
	:param r:   Right coord
	:return:
	"""
	if np.linalg.norm(np.array(l) - np.array(r)) > RCB_THRESHOLD:
		# Calculate midpoint between two bounds
		midpoint = tuple((np.array(l) + np.array(r)) / 2)

		# Run simulation
		classification = sample_coord(lmp, *midpoint)

		# Determine if we're to the left or right
		if REGIMES.index(classification) == 0:
			# We're to the left, make current coord the left bound and recurse
			return recursive_bisect(lmp, midpoint, r)
		elif REGIMES.index(classification) == 1:
			# We're to the right, make current coord the right bound and recurse
			return recursive_bisect(lmp, l, midpoint)
		else:
			raise RuntimeError("This should not happen")


def bisection_job(l: Tuple[float, float], r: Tuple[float, float]):
	"""
	Instantiates a LAMMPS object and runs equilibration.
	Wraps recursive_bisect().
	:param l: Left coord
	:param r: Right coord
	:return:
	"""
	# Calculate midpoint between two bounds for equilibration
	midpoint = tuple((np.array(l) + np.array(r)) / 2)

	# Instantiate LAMMPS object
	lmp = lammps()

	lmp.command('variable epp equal {}'.format(midpoint[0]))
	lmp.command('variable eps equal {}'.format(midpoint[1]))

	# Run 'header' of equilibration input file
	lmp.file('../in.b_equi_header')
	# Equilibrate
	lmp.file('../in.b_equi_run')

	# Start recursive bisectioning
	recursive_bisect(lmp, l, r)

	lmp.close()


if __name__ == '__main__':
	# Create pool of number of cores workers
	with Pool() as p:
		outputList = p.starmap(bisection_job, pairs)
