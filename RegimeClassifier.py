"""
Analyses density profiles and radial distribution functions to classify the system in one of three sorption states.
0: No sorption
1: Adsorption, no absorption
2: Adsorption,    absorption
"""

import re
from io import StringIO
from sys import path
from typing import Sequence
path.append("../../shared_python_scripts/")

import numpy as np
from scipy.signal import find_peaks_cwt, savgol_filter

from BrushDensityParser import BrushDensityParser


class RegimeClassifier:
	FILENAME_RDF = 'rdf.dat'
	FILENAME_DENS_POLY = 'PolyDens.dat'
	FILENAME_DENS_SOLV = 'SolvDens.dat'

	CWT_WIDTHS = range(6, 45)
	SG_WINDOW = 21
	SG_ORDER = 2

	def __init__(self, directory: str, filename_poly: str = FILENAME_DENS_POLY, filename_solvent: str = FILENAME_DENS_SOLV):
		self.directory: str = directory
		bdp = BrushDensityParser()

		densPoly = bdp.loadDensity(directory + '/' + filename_poly)
		densSolv = bdp.loadDensity(directory + '/' + filename_solvent)

		# time-averaged profiles
		self.poly_ta: np.ndarray = np.mean(densPoly, axis=0)
		self.solv_ta: np.ndarray = np.mean(densSolv, axis=0)

	def parse_rdf(self, filename: str = FILENAME_RDF) -> np.ndarray:
		# Use regex to strip the timestep lines
		with open(self.directory + '/' + filename) as f:
			p = re.compile(r'^\d+ \d+\n', re.MULTILINE)
			string = p.sub('', f.read())

		data = np.loadtxt(StringIO(string), usecols=(0, 3, 5))

		# The data array is a '2D flattened' representation of a 3D array
		# (the third dimension being the time). We need to first get the number of
		# bins and then reshape the array using that number

		# Get the index where the second bin is 1 (that is the number of bins)
		numBins = np.nonzero(data[:, 0] == 1)[0][1]

		reshaped = data.reshape((-1, numBins, 3))

		# We're only really interested in the coordination numbers of the last bins
		return reshaped[:, -1, 1:3]

	def get_coordination_numbers(self, filename: str = FILENAME_RDF) -> np.ndarray:
		"""
		:return: a two-element array containing the coordination number of solvent with polymer,
		         and the coordination number of solvent with itself
		"""
		data = self.parse_rdf(filename)
		return np.mean(data[5:-1, :], axis=0)

	def get_ratio(self, filename: str = FILENAME_RDF) -> np.ScalarType:
		data_avg = self.get_coordination_numbers(filename)
		return data_avg[1] / data_avg[0]

	def get_overlap(self) -> np.ScalarType:
		"""
		Calculate the overlap integral between the polymer density and solvent density profiles.
		:return:
		"""
		return np.trapz(self.solv_ta[:, 2] * self.poly_ta[:, 2])

	def get_poly_inflection(self, window: int = SG_WINDOW, order: int = SG_ORDER) -> np.ScalarType:
		"""
		Finds the inflection point of the polymer density profile by calculating the gradient using a Savitsky-Golay
		filter and getting the index of the minimum element in that array.
		:param window: Window size of the Savitsky-Golay filter
		:param order: Order of the polynomial fitted by the Savitsky-Golay filter
		:return: Index of the inflection point
		"""
		# Smooth using Savitzky–Golay
		poly_ta_smoothed = savgol_filter(self.poly_ta[:, 2], window, order, deriv=1)
		# Inflection point is minimum of first derivative
		return poly_ta_smoothed.argmin()

	def get_solv_peak(self, cwt_widths: Sequence = CWT_WIDTHS) -> np.ScalarType:
		"""
		Finds the peak in the solvent density profile with the help of a continuous wavelet transform smoothing.
		:param cwt_widths: Array with widths that are used for the wavelets that the data is convolved with.
		                   Make smallest value smaller for more precise peak localisation, make largest value larger
		                   for more smoothing.
		:return: Index of the peak
		"""
		# Find peak of the solvent profile
		return find_peaks_cwt(self.solv_ta[:, 2], cwt_widths)[0]

	def get_classification(self, overlap_threshold=0.2, cwt_widths: Sequence = CWT_WIDTHS, window: int = SG_WINDOW,
	                       order: int = SG_ORDER) -> int:
		"""
		Get the regime classification the system is in, determined by the combination of the overlap integral and
		location of the solvent peak with respect to the polymer surface (inflection point in the density profile)
		:param overlap_threshold: Threshold for the overlap integral below which the system is considered to have "no sorption"
		:param cwt_widths: see get_solv_peak()
		:param window: see get_poly_inflection()
		:param order: see get_poly_inflection()
		:return: Classification (0, 1, or 2)
		"""
		if self.get_overlap() < overlap_threshold:
			return 0
		# Overlap > threshold, so we have sorption
		if self.get_solv_peak(cwt_widths) > self.get_poly_inflection(window, order):
			return 1
		# Solvent peak is right of the polymer inflection point, so we have adsorption
		return 2
