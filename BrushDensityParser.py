"""
Exports the BrushDensityParser class.
"""

import re
from io import StringIO

import numpy as np


class BrushDensityParser:
	"""
	Parses a LAMMPS ave/chunk output file.
	"""

	@staticmethod
	def load_density(filename: str) -> np.ndarray:
		"""
		:param filename: String containing the filename of the density file to parse.
		:return: A 3d ndarray with shape (a, b, 3), representing density profiles at different timesteps with a being
				 the number of temporal profiles and b being the number of spatial chunks in a profile. One row is a
				 tuple of (chunk #, spatial distance, density).
		"""
		# Use regex to strip the timestep lines
		with open(filename) as f:
			p = re.compile(r'\n\d.*')
			string = p.sub('', f.read())

		data = np.loadtxt(StringIO(string), usecols=(0, 1, 3))

		# The data array is a '2D flattened' representation of a 3D array
		# (the third dimension being the time). We need to first get the number of
		# chunks and then reshape the array using that number

		# Get the index where the second chunk is 1 (that is the number of chunks)
		num_chunks = np.nonzero(data[:, 0] == 1)[0][1]

		return data.reshape((-1, num_chunks, 3))
