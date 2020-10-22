#!/usr/bin/env python3

""" Copyright © 2020 Borys Olifirov

Functions for cell detecting and ROI extraction.
Functions for embrane detection and membrane regions extraction with hysteresis filter.
Optimysed for widefield neuron image.

"""

import os
import logging

import numpy as np
import numpy.ma as ma

from skimage.external import tifffile
from skimage import filters
from skimage import measure
from skimage import segmentation

from scipy import ndimage as ndi
from scipy.ndimage import measurements as msr



def backRm(img, edge_lim=20, dim=3):
    """ Background extraction in TIFF series

    For confocal Z-stacks only!
    dem = 2 for one frame, 3 for z-stack

    """
    if dim == 3:
        edge_stack = img[:,:edge_lim,:edge_lim]
        mean_back = np.mean(edge_stack)

        logging.info('Mean background, {} px region: {:.3f}'.format(edge_lim, mean_back))

        img_out = np.copy(img)
        img_out = img_out - mean_back
        img_out[img_out < 0] = 0

        return img_out
    elif dim == 2:
        edge_fragment = img[:edge_lim,:edge_lim]
        mean_back = np.mean(edge_fragment)

        logging.info('Mean background, %s px region: %s' % (edge_lim, mean_back))

        img = np.copy(img)
        img = img - mean_back
        img[img < 0] = 0

        return img


def hystMask(img, high=0.8, low=0.2, sigma=3):
    """ Function for neuron region detection with hysteresis threshold algorithm.

    img - input image with higest intensity;
    gen_high - float,  general upper threshold for hysteresis algorithm (percentage of maximum frame intensity);
    sigma - int, sd for gaussian filter.

    Returts cell boolean mask for input frame.

    """
    img_gauss = filters.gaussian(img, sigma=sigma)
    num = 10
    while num > 1:
        mask = filters.apply_hysteresis_threshold(img_gauss,
                                                  low=np.max(img_gauss)*high,
                                                  high=np.max(img_gauss)*low)
        a, num = ndi.label(mask)
        low -= 0.01
    logging.info('Lower limit for hystMask={}'.format(round(low, 2)))
    return mask


def sDerivate(series, mask, sd_area=50, sigma=4, mean_reate=1, interval=0):
    """ Calculating derivative image series (difference between current and previous frames).

    Pixels greater than noise sd set equal to 1;
    Pixels less than -noise sd set equal to -1.

    """
    gauss_series = [filters.gaussian(img, sigma=sigma) for img in series]
    logging.info('Derivate sigma={}'.format(sigma))
    derivete_series = []
    i = 1
    while i < len(gauss_series):
        frame_sd = np.std(gauss_series[i][:50, :50])

        derivete_frame = gauss_series[i] - gauss_series[i-1]
        derivete_frame[derivete_frame > frame_sd] = 1
        derivete_frame[derivete_frame < -frame_sd] = -1

        derivete_series.append(ma.masked_where(~mask, derivete_frame))
        i += 1
    logging.info('Derivate len={}'.format(len(derivete_series)))
    return derivete_series


def apply_hysteresis_threshold(image, low, high):
    low = np.clip(low, a_min=None, a_max=high)  # ensure low always below high
    mask_low = image > low
    mask_high = image > high
    # Connected components of mask_low
    labels_low, num_labels = ndi.label(mask_low)
    # Check which connected components contain pixels from mask_high
    sums = ndi.sum(mask_high, labels_low, np.arange(num_labels + 1))
    connected_to_high = sums > 0
    thresholded = connected_to_high[labels_low]

    return thresholded



if __name__=="__main__":
    pass


# That's all!