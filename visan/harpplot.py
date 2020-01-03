# Copyright (C) 2002-2020 S[&]T, The Netherlands.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Mapping of HARP Product data to Plot input
"""

import re
import coda
import harp
import numpy


UNPREFERED_PATTERNS = [
    "index", "collocation_index", "orbit_index", ".*subindex", "scan_direction_type",
    "datetime.*",
    "sensor_.*",
    ".*validity",
    ".*_uncertainty.*",
    ".*_apriori.*",
    ".*_amf.*",
    "wavenumber$",
    "wavelength$",
    ".*latitude.*",
    ".*longitude.*",
    ".*altitude",
    ".*geoid_height",
    ".*geopotential",
    ".*pressure",
    ".*_angle"
]


def get_prefered_value(values, unprefered_patterns):
    if unprefered_patterns:
        value = get_prefered_value([value for value in values if not re.match(unprefered_patterns[0], value)],
                                   unprefered_patterns[1:])
        if value is not None:
            return value
    if values:
        return values[0]
    return None


def get_attributes(product):
    # we return all scalars and 1D (time dependent) variables
    def attr_value(value, variable):
        if hasattr(variable, "unit"):
            if " since " in variable.unit:
                # this is a time value
                base, epoch = variable.unit.split(" since ")
                if base in ["s", "seconds", "days"]:
                    if base == "days":
                        value *= 86400
                    formats = "yyyy-MM-dd HH:mm:ss.SSSSSS|yyyy-MM-dd HH:mm:ss|yyyy-MM-dd"
                    value = value + coda.time_string_to_double(formats, epoch)
                    return coda.time_to_string(value)
            return "%s [%s]" % (str(value), variable.unit)
        return str(value)

    attr = {}
    for name in list(product):
        if len(product[name].dimension) == 0:
            attr[name] = attr_value(product[name].data, product[name])
        elif len(product[name].dimension) == 1 and product[name].dimension[0] == 'time':
            attr[name] = [attr_value(value, product[name]) for value in product[name].data]
    return attr


def get_midpoint_axis_from_bounds(bounds_variable, log=False):
    if bounds_variable.data.shape[-1] != 2 or bounds_variable.dimension[-1] is not None:
        raise ValueError("bounds variable should end with independent dimension of length 2")
    if log:
        data = numpy.exp((numpy.log(bounds_variable.data[..., 0]) + numpy.log(bounds_variable.data[..., 1])) / 2.0)
    else:
        data = (bounds_variable.data[..., 0] + bounds_variable.data[..., 1]) / 2.0
    return harp.Variable(data, bounds_variable.dimension[:-1], bounds_variable.unit)


def PlotDataForProduct(product, value=None):
    if not isinstance(product, harp.Product):
        raise TypeError("Expecting a HARP product")

    variable_names = []

    for name in list(product):
        if len(product[name].dimension) == 0 or len(product[name].dimension) > 2:
            continue
        if not isinstance(product[name].data, (numpy.ndarray, numpy.generic)):
            continue
        if product[name].data.dtype.char in ['O', 'S']:
            continue
        if product[name].dimension[0] != 'time':
            continue
        if len(product[name].dimension) == 2 and product[name].dimension[1] not in ['spectral', 'vertical']:
            continue
        variable_names += [name]

    if value is not None:
        if value not in list(product):
            raise ValueError("product variable does not exist ('%s')" % value)
        if value not in variable_names:
            raise ValueError("product variable is not plottable ('%s')" % value)
    else:
        value = get_prefered_value(variable_names, UNPREFERED_PATTERNS)

    if value is None:
        raise ValueError("HARP product is not plotable")

    xdata = None
    ydata = product[value]
    attr = {}
    location = []
    prop = {'title': value.replace('_', ' '), 'name': value}

    if len(product[value].dimension) == 2:
        if product[value].dimension[1] == 'spectral':
            if 'wavelength' in product:
                xdata = product['wavelength']
            elif 'wavenumber' in product:
                xdata = product['wavenumber']
            if xdata is None:
                raise ValueError("Could not determine x-axis for spectral data ('%s')" % value)
        else:
            # product[value].dimension[1] == 'vertical'
            # swap axis
            xdata = ydata
            ydata = None
            if 'altitude' in product:
                ydata = product['altitude']
            elif 'altitude_bounds' in product:
                ydata = get_midpoint_axis_from_bounds(product['altitude_bounds'])
            elif 'pressure' in product:
                ydata = product['pressure']
                prop["ylog"] = True
            elif 'pressure_bounds' in product:
                ydata = get_midpoint_axis_from_bounds(product['pressure_bounds'], log=True)
                prop["ylog"] = True
            if ydata is None:
                raise ValueError("Could not determine y-axis for vertical profile data ('%s')" % value)
        attr = get_attributes(product)
    else:
        if 'datetime' in product:
            xdata = product['datetime']
        elif 'datetime_start' in product:
            xdata = product['datetime_start']
        elif 'datetime_stop' in product:
            xdata = product['datetime_stop']
        if xdata is None:
            raise ValueError("Could not determine x-axis for time-series data ('%s')" % value)

    if 'latitude_bounds' in product and 'longitude_bounds' in product:
        location = [product.latitude_bounds.data, product.longitude_bounds.data]
    elif 'latitude' in product and 'longitude' in product:
        location = [product.latitude.data, product.longitude.data]

    try:
        prop['xlabel'] = xdata.unit
    except AttributeError:
        pass
    try:
        prop['ylabel'] = ydata.unit
    except AttributeError:
        pass

    return (xdata.data, ydata.data, attr, location, prop)


kPointData = 0
kSwathData = 1
kGridData = 2


def WorldPlotDataForProduct(product, locationOnly, value=None):
    if not isinstance(product, harp.Product):
        raise TypeError("Expecting a HARP product")

    data_type = kPointData
    latitude = None
    longitude = None
    if 'latitude_bounds' in list(product) and 'longitude_bounds' in list(product):
        latitude_bounds = product['latitude_bounds']
        longitude_bounds = product['longitude_bounds']
        if len(latitude_bounds.dimension) != len(longitude_bounds.dimension):
            raise ValueError("latitude and longitude bounds should have same number of dimensions")
        if latitude_bounds.dimension[-1] is not None or longitude_bounds.dimension[-1] is not None:
            raise ValueError("last dimension for latitude and longitude bounds should be independent")
        if len(latitude_bounds.dimension) > 1 and latitude_bounds.dimension[-2] == 'latitude' and \
                longitude_bounds.dimension[-2] == 'longitude':
            if len(latitude_bounds.dimension) == 3:
                if latitude_bounds.dimension[0] != 'time' or longitude_bounds.dimension[0] != 'time':
                    raise ValueError("first dimension for latitude and longitude bounds should be the time dimension")
            else:
                if len(latitude_bounds.dimension) != 2:
                    raise ValueError("latitude and longitude bounds should be "
                                     "two or three dimensional for gridded data")
            if latitude_bounds.data.shape[-1] != 2 or longitude_bounds.data.shape[-1] != 2:
                raise ValueError("independent dimension of latitude and longitude bounds should have "
                                 "length 2 for gridded data")
            data_type = kGridData
            latitude = get_midpoint_axis_from_bounds(latitude_bounds)
            longitude = get_midpoint_axis_from_bounds(longitude_bounds)
        elif not locationOnly:
            if len(latitude_bounds.dimension) != 2:
                raise ValueError("latitude and longitude bounds should be two dimensional for non-gridded data")
            if latitude_bounds.dimension[0] != 'time' or longitude_bounds.dimension[0] != 'time':
                raise ValueError("first dimension for latitude and longitude bounds should be the time dimension")
            if latitude_bounds.data.shape != longitude_bounds.data.shape:
                raise ValueError("latitude and longitude bounds should have the same dimension lengths")
            data_type = kSwathData
            latitude = latitude_bounds
            longitude = longitude_bounds
    if data_type != kSwathData and 'latitude' in list(product) and 'longitude' in list(product):
        latitude = product['latitude']
        longitude = product['longitude']
        if len(latitude.dimension) != len(longitude.dimension):
            raise ValueError("latitude and longitude should have same number of dimensions")
        if len(latitude.dimension) > 0 and latitude.dimension[-1] == 'latitude' and \
                longitude.dimension[-1] == 'longitude':
            # if we have both lat/lon center and lat/lon bounds then use the center lat/lon for the grid axis
            if len(latitude.dimension) == 2:
                if latitude.dimension[0] != 'time' or longitude.dimension[0] != 'time':
                    raise ValueError("first dimension for latitude and longitude should be the time dimension")
            else:
                if len(latitude.dimension) != 1:
                    raise ValueError("latitude and longitude should be one or two dimensional")
            data_type = kGridData
        else:
            if len(latitude.dimension) != 1:
                raise ValueError("latitude and longitude should be one dimensional")
            if latitude.dimension[0] != 'time' or longitude.dimension[0] != 'time':
                raise ValueError("first dimension for latitude and longitude should be the time dimension")
            data_type = kPointData
    if latitude is None or longitude is None:
        raise ValueError("HARP product has no latitude/longitude information")

    if locationOnly:
        value = None
    else:
        variable_names = []

        for name in list(product):
            if not isinstance(product[name].data, (numpy.ndarray, numpy.generic)):
                continue
            if product[name].data.dtype.char in ['O', 'S']:
                continue
            if data_type == kGridData:
                if len(product[name].dimension) < 2 or len(product[name].dimension) > 3:
                    continue
                if product[name].dimension[-2] != 'latitude':
                    continue
                if product[name].dimension[-1] != 'longitude':
                    continue
                if len(product[name].dimension) == 3 and product[name].dimension[0] != 'time':
                    continue
            else:
                if len(product[name].dimension) != 1:
                    continue
                if product[name].dimension[0] != 'time':
                    continue
            variable_names += [name]

        if value is not None:
            if value not in list(product):
                raise ValueError("product variable does not exist ('%s')" % value)
            if value not in variable_names:
                raise ValueError("product variable is not plottable ('%s')" % value)
        else:
            value = get_prefered_value(variable_names, UNPREFERED_PATTERNS)

    data = None
    attr = {}
    prop = {}

    if data_type == kGridData:
        attr = get_attributes(product)
        if value is None:
            raise ValueError("HARP product has no variable to use for gridded plot")

    if value is not None:
        data = product[value].data
        prop["name"] = value
        prop["colorbartitle"] = value.replace('_', ' ')
        try:
            prop["colorbartitle"] += " [" + product[value].unit + "]"
        except AttributeError:
            pass

    return (data_type, data, latitude.data, longitude.data, attr, prop)
