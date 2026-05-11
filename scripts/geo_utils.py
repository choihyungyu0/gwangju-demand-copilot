from __future__ import annotations

import numpy as np


EARTH_RADIUS_M = 6_371_000


def haversine_distance(lat1, lon1, lat2, lon2):
    """Return Haversine distance in meters.

    Inputs may be scalars, pandas Series, or numpy arrays. The function returns a
    scalar for scalar input and a numpy array for vector input.
    """
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return EARTH_RADIUS_M * c
