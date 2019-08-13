"""
Exports the RegimeClassifier class.
"""

from typing import Sequence

import numpy as np
from scipy.signal import find_peaks_cwt, savgol_filter

from BrushDensityParser import BrushDensityParser


class RegimeClassifier:
	"""
	Analyses density profiles and radial distribution functions to classify the system in one of three sorption states.
	0: No sorption
	1: Adsorption, no absorption
	2: Adsorption,    absorption
	"""
	FILENAME_DENS_POLY = 'PolyDens.dat'
	FILENAME_DENS_SOLV = 'SolvDens.dat'

	CWT_WIDTHS = range(1, 15)
	SG_WINDOW = 21
	SG_ORDER = 2
	SOLV_TRIM = 12

	def __init__(self, directory: str, filename_poly: str = FILENAME_DENS_POLY,
	             filename_solvent: str = FILENAME_DENS_SOLV):
		"""
		:param directory: String containing the path to the base directory containing the files.
		:param filename_poly: String containing the filename of the polymer density file.
		:param filename_solvent: String containing the filename of the solvent density file.
		"""
		self.directory: str = directory
		bdp = BrushDensityParser()

		dens_poly = bdp.load_density(directory + '/' + filename_poly)
		dens_solv = bdp.load_density(directory + '/' + filename_solvent)

		# time-averaged profiles
		self.poly_ta: np.ndarray = np.mean(dens_poly, axis=0)
		self.solv_ta: np.ndarray = np.mean(dens_solv, axis=0)

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

	def get_solv_peak(self, cwt_widths: Sequence = CWT_WIDTHS, trim: int = SOLV_TRIM) -> np.ScalarType:
		"""
		Finds the peak in the solvent density profile with the help of a continuous wavelet transform smoothing.
		:param cwt_widths: Array with widths that are used for the wavelets that the data is convolved with.
		                   Make smallest value smaller for more precise peak localisation, make largest value larger
		                   for more smoothing.
		:param trim: Number of indices to trim from the beginning (left part) of the solvent profile.
		:return: Index of the peak
		"""
		# Find peaks of the solvent profile
		peaks = find_peaks_cwt(self.solv_ta[trim:, 2], cwt_widths) + trim

		# Get highest peak
		return peaks[self.solv_ta[peaks, 2].argmax()]

	def get_classification(self, overlap_threshold=0.50, cwt_widths: Sequence = CWT_WIDTHS, trim: int = SOLV_TRIM,
	                       window: int = SG_WINDOW, order: int = SG_ORDER) -> int:
		"""
		Get the regime classification the system is in, determined by the combination of the overlap integral and
		location of the solvent peak with respect to the polymer surface (inflection point in the density profile)
		:param overlap_threshold: Threshold for the overlap integral below which the system is considered to have "no sorption"
		:param cwt_widths: see get_solv_peak()
		:param trim: Number of indices to trim from the beginning (left part) of the solvent profile.
		:param window: see get_poly_inflection()
		:param order: see get_poly_inflection()
		:return: Classification (0, 1, or 2)
		"""
		if self.get_overlap() < overlap_threshold:
			return 0
		# Overlap > threshold, so we have sorption
		if self.get_solv_peak(cwt_widths, trim) > self.get_poly_inflection(window, order):
			return 1
		# Solvent peak is right of the polymer inflection point, so we have adsorption
		return 2
