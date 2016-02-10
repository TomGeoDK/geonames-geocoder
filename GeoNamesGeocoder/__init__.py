# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoNamesGeocoder
                                 A QGIS plugin
 Geo-coding of places, based on a local copy of the GeoNames database
                             -------------------
        begin                : 2016-02-09
        copyright            : (C) 2016 by Thomas Becker (Aarhus Univiersity)
        email                : thob@envs.au.dk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeoNamesGeocoder class from file GeoNamesGeocoder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .geonames_geocoder import GeoNamesGeocoder
    return GeoNamesGeocoder(iface)
