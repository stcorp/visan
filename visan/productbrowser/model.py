# Copyright (C) 2002-2021 S[&]T, The Netherlands.
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

import coda
import copy
import wx
import os.path
import weakref


(TYPE_INT8, TYPE_UINT8, TYPE_INT16, TYPE_UINT16, TYPE_INT32, TYPE_UINT32, TYPE_INT64, TYPE_UINT64,
 TYPE_FLOAT32, TYPE_FLOAT64, TYPE_CHAR, TYPE_STRING, TYPE_BYTES, TYPE_NO_DATA, TYPE_VSF_INTEGER, TYPE_TIME,
 TYPE_COMPLEX, TYPE_ARRAY, TYPE_RECORD, TYPE_UNKNOWN) = list(range(20))

_CodaNativeTypeDictionary = {coda.coda_native_type_int8: TYPE_INT8,
                             coda.coda_native_type_uint8: TYPE_UINT8,
                             coda.coda_native_type_int16: TYPE_INT16,
                             coda.coda_native_type_uint16: TYPE_UINT16,
                             coda.coda_native_type_int32: TYPE_INT32,
                             coda.coda_native_type_uint32: TYPE_UINT32,
                             coda.coda_native_type_int64: TYPE_INT64,
                             coda.coda_native_type_uint64: TYPE_UINT64,
                             coda.coda_native_type_float: TYPE_FLOAT32,
                             coda.coda_native_type_double: TYPE_FLOAT64,
                             coda.coda_native_type_char: TYPE_CHAR,
                             coda.coda_native_type_string: TYPE_STRING,
                             coda.coda_native_type_bytes: TYPE_BYTES}

_CodaSpecialTypeDictionary = {coda.coda_special_no_data: TYPE_NO_DATA,
                              coda.coda_special_vsf_integer: TYPE_VSF_INTEGER,
                              coda.coda_special_time: TYPE_TIME,
                              coda.coda_special_complex: TYPE_COMPLEX}

_TypeDictionary = {TYPE_INT8: "int8",
                   TYPE_UINT8: "uint8",
                   TYPE_INT16: "int16",
                   TYPE_UINT16: "uint16",
                   TYPE_INT32: "int32",
                   TYPE_UINT32: "uint32",
                   TYPE_INT64: "int64",
                   TYPE_UINT64: "uint64",
                   TYPE_FLOAT32: "float",
                   TYPE_FLOAT64: "double",
                   TYPE_CHAR: "char",
                   TYPE_STRING: "string",
                   TYPE_BYTES: "bytes",
                   TYPE_NO_DATA: "no data",
                   TYPE_VSF_INTEGER: "vsf integer",
                   TYPE_TIME: "time",
                   TYPE_COMPLEX: "complex",
                   TYPE_ARRAY: "array",
                   TYPE_RECORD: "record",
                   TYPE_UNKNOWN: "unknown"}

icons = None
iconImageList = None
iconDictionary = None
expandedIconDictionary = None


class CorruptProductError(Exception):

    pass


class Node(object):

    def __init__(self, type=TYPE_UNKNOWN):
        self.parent = None
        self.cursor = None

        self.name = ""
        self.real_name = ""
        self.type = type

        # only record fields have an associated availability
        # for all other Nodes available is always True.
        self.available = True

        # only record fields can be hidden, for all other
        # Nodes hidden is always False.
        self.hidden = False

    def initialize(self):
        assert self.cursor, "cursor should be set before calling initialize()"

    def _path(self, path):
        path.append(self)

        if self.parent is None:
            path.reverse()
            return path
        else:
            return self.parent._path(path)

    def path(self):
        return self._path([])

    # we cache the bit size here. this is not very clean, because only
    # the CODA backend has meaningful bit sizes. however, requesting
    # a bit size for other backends is legal (result will be -1) and
    # it saves a large amount of time while navigating through a product.
    def getBitSize(self):
        assert self.cursor, "cursor should be set before calling getBitSize()"

        try:
            size = self._bitSize
        except AttributeError:
            # if an error occurs while trying to determine the
            # bit size, the _bitSize attribute is not added to the
            # Node instance. this is appropriate, because the bit size
            # is still unknown.
            size = coda.cursor_get_bit_size(self.cursor)
            self._bitSize = size

        return size


class StringNode(Node):

    def __init__(self):
        Node.__init__(self, TYPE_STRING)
        self._length = -1

    def initialize(self):
        Node.initialize(self)
        self._length = coda.cursor_get_string_length(self.cursor)

    def __len__(self):
        return self._length


class CompoundNode(Node):

    def __init__(self, type=TYPE_UNKNOWN):
        assert type in (TYPE_UNKNOWN, TYPE_RECORD, TYPE_ARRAY)
        Node.__init__(self, type)
        self._count = -1

    def initialize(self):
        Node.initialize(self)
        self._count = coda.cursor_get_num_elements(self.cursor)

    def __len__(self):
        return self._count


class RecordNode(CompoundNode):

    def __init__(self):
        CompoundNode.__init__(self, TYPE_RECORD)
        self._fields = None

    def dirty(self):
        return self._fields is None

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError("index should be an integer")

        if self.dirty():
            raise ValueError("cannot retrieve field information from dirty record")

        if key < 0 or key > len(self._fields):
            raise IndexError("field index out of range")

        return self._fields[key]


class ArrayNode(CompoundNode):

    def __init__(self, base=TYPE_UNKNOWN):
        CompoundNode.__init__(self, TYPE_ARRAY)
        self.base = base
        self.dimensions = None

    def initialize(self):
        CompoundNode.initialize(self)
        self.dimensions = coda.cursor_get_array_dim(self.cursor)

    def isRankZero(self):
        return (len(self.dimensions) == 0)

    def isObjectArray(self):
        return isinstance(self, ObjectArrayNode)


class ObjectArrayNode(ArrayNode):

    def __init__(self, base=TYPE_UNKNOWN):
        ArrayNode.__init__(self, base)
        self.cache = {}

    def initialize(self):
        ArrayNode.initialize(self)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError("index should be an integer")

        if key < 0 or key > len(self):
            raise IndexError("array index out of range")

        return _RetrieveArrayElement(self, key)


def NodeFactory(cursor):
    nodeCodaType = coda.cursor_get_type(cursor)
    nodeCodaClass = coda.type_get_class(nodeCodaType)

    type = TranslateCodaType(nodeCodaClass, nodeCodaType)

    if type == TYPE_RECORD:
        return RecordNode()

    elif (type == TYPE_ARRAY):
        baseCodaType = coda.type_get_array_base_type(nodeCodaType)
        baseCodaClass = coda.type_get_class(baseCodaType)

        baseType = TranslateCodaType(baseCodaClass, baseCodaType)

        if ((baseType == TYPE_RECORD) or (baseType == TYPE_ARRAY)):
            return ObjectArrayNode(baseType)
        else:
            return ArrayNode(baseType)

    elif type == TYPE_STRING:
        return StringNode()

    else:
        return Node(type)


def TranslateCodaType(nodeClass, nodeType):
    if nodeClass == coda.coda_record_class:
        return TYPE_RECORD

    elif (nodeClass == coda.coda_array_class):
        return TYPE_ARRAY

    elif ((nodeClass == coda.coda_integer_class) or (nodeClass == coda.coda_real_class) or
          (nodeClass == coda.coda_text_class) or (nodeClass == coda.coda_raw_class)):

        # scalar type.
        nodeReadType = coda.type_get_read_type(nodeType)

        if nodeReadType == coda.coda_native_type_not_available:
            raise TypeError("TranslateCodaType():: coda_native_type_not_available encountered.")
        else:
            try:
                return _CodaNativeTypeDictionary[nodeReadType]
            except KeyError:
                return TYPE_UNKNOWN

    elif nodeClass == coda.coda_special_class:
        # special type.
        nodeSpecialType = coda.type_get_special_type(nodeType)

        try:
            return _CodaSpecialTypeDictionary[nodeSpecialType]
        except KeyError:
            return TYPE_UNKNOWN
    else:
        return TYPE_UNKNOWN


def RetrieveFieldInfo(node):
    assert node.dirty(), "_RetrieveFieldInfo() should only be called on dirty nodes."

    node._fields = []

    if len(node) > 0:
        try:
            cursor = copy.deepcopy(node.cursor)
            nodeCodaType = coda.cursor_get_type(node.cursor)
            coda.cursor_goto_first_record_field(cursor)
            for i in range(0, len(node)):
                field = NodeFactory(cursor)
                node._fields.append(field)
                field.parent = weakref.proxy(node)
                field.cursor = copy.deepcopy(cursor)
                field.name = coda.type_get_record_field_name(nodeCodaType, i)
                field.real_name = coda.type_get_record_field_real_name(nodeCodaType, i)
                field.available = (coda.cursor_get_record_field_available_status(node.cursor, i) == 1)
                field.hidden = (coda.type_get_record_field_hidden_status(nodeCodaType, i) == 1)
                field.initialize()

                if i < len(node) - 1:
                    coda.cursor_goto_next_record_field(cursor)
        except coda.CodacError as ex:
            # restore state
            node._fields = None
            raise CorruptProductError("[CODA] %s" % (str(ex),))


def _RetrieveArrayElement(node, index):
    assert index >= 0, "Trying to retrieve element at unspecified index (-1)"

    # try to retrieve the current element from the cache.
    try:
        return node.cache[index]
    except KeyError:
        # cache miss.
        pass

    # optimisation suggested by Sander.
    previousElement = None
    if index > 0:
        try:
            previousElement = node.cache[index - 1]
        except KeyError:
            # cache miss.
            pass

    # try to retrieve the node
    try:
        if previousElement:
            cursor = copy.deepcopy(previousElement.cursor)
            # goto_next_array_element is much faster than goto_array_element
            # for large arrays.
            coda.cursor_goto_next_array_element(cursor)
        else:
            cursor = copy.deepcopy(node.cursor)
            coda.cursor_goto_array_element_by_index(cursor, index)

        element = NodeFactory(cursor)
        element.parent = weakref.proxy(node)
        element.cursor = cursor
        element.name = GetMultiDimensionalIndex(node, index)
        element.initialize()
    except coda.CodacError as ex:
        raise CorruptProductError("[CODA] %s" % (str(ex),))

    # cache element
    node.cache[index] = element
    return element


def RetrieveAttributes(node):
    cursor = copy.deepcopy(node.cursor)

    try:
        coda.cursor_goto_attributes(cursor)
        attributes = NodeFactory(cursor)
        attributes.cursor = cursor
        attributes.name = "attributes"
        attributes.initialize()
        return attributes

    except coda.CodacError as ex:
        raise CorruptProductError("[CODA] %s" % (str(ex),))


def GetMultiDimensionalIndex(node, index):
    if node.isRankZero():
        assert index == 0, "Rank-0 array can only be indexed with 0"
        return [0]
    else:
        multiDimensionalIndex = []
        for i in reversed(list(range(1, len(node.dimensions)))):
            multiDimensionalIndex.append(index % node.dimensions[i])
            index -= index % node.dimensions[i]
            index /= node.dimensions[i]
        multiDimensionalIndex.append(index)
        multiDimensionalIndex.reverse()
        return multiDimensionalIndex


def GetNodeAsListItem(index, node, data=None):
    item = wx.ListItem()
    if data:
        item.SetMask(wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_DATA)
        item.SetData(data)
    else:
        item.SetMask(wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE)

    item.SetId(index)
    item.SetText(node.name)
    item.SetImage(GetNodeIcon(node, iconDictionary))

    if node.hidden:
        item.SetFont(item.GetFont().Italic())

    if (not node.available) or (isinstance(node, CompoundNode) and len(node) == 0):
        item.SetTextColour("light grey")

    return item


def GetTypeAsString(type):
    try:
        return _TypeDictionary[type]
    except KeyError:
        return "unknown"


def GetDataAsString(type, data, maxLength=-1):
    assert data is not None, "\"data\" argument should not be None."

    if type == TYPE_STRING or type == TYPE_CHAR:
        if maxLength >= 0 and len(data) > maxLength:
            return "<string of length %u>" % (len(data),)
        else:
            return "\"%s\"" % (data,)

    elif type == TYPE_TIME:
        try:
            return coda.time_to_string(data)
        except coda.CodacError:
            return "<invalid time value>"

    elif type == TYPE_BYTES:
        # convert length in bytes to length in characters ("0x%x " per byte).
        if maxLength >= 0 and (data.size * 5) > maxLength:
            return "<data block of %u byte(s)>" % (data.size,)
        elif data.size > 0:
            result = ""
            for byte in data[:-1]:
                result += "0x%x " % (byte,)
            result += "0x%x" % (data[-1],)
            return result
        else:
            return ""

    elif type == TYPE_RECORD:
        # return a key-value list of the fields between braces
        if len(data) == 0:
            return "<empty record>"
        result = "("
        for field in data._registeredFields:
            result += "%s=%s, " % (field, str(data.__dict__[field]),)
        result = result[:-2] + ")"
        if maxLength >= 0 and len(result) > maxLength:
            return "<record with %u field%s>" % (len(data), "s" if len(data) != 1 else "")
        return result

    else:
        return str(data)


def GetPathAsString(path):
    if len(path) == 0:
        return "/"
    else:
        pathString = "/"
        for place in path[:-1]:
            pathString += str(place.name)
            if place.type == TYPE_RECORD and pathString != "/":
                pathString += "/"
        pathString += str(path[-1].name)
        return pathString


def GetNodeIcon(node, dict):
    if not dict:
        return 0
    try:
        return dict[node.type]
    except KeyError:
        return 0


# code to initialize a 'standard icon library'
def InitIcons():
    global icons, iconImageList, iconDictionary, expandedIconDictionary

    if not icons:
        iconDir = wx.Config.Get().Read("DirectoryLocation/ApplicationData")
        icons = []
        iconImageList = wx.ImageList(16, 16)

        tmp = wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16))
        icons.append(tmp)
        ICON_DEFAULT = iconImageList.Add(tmp)

        tmp = wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE, wx.ART_OTHER, (16, 16))
        icons.append(tmp)
        ICON_UNAVAILABLE = iconImageList.Add(tmp)

        tmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16))
        icons.append(tmp)
        ICON_FOLDER = iconImageList.Add(tmp)

        tmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16))
        icons.append(tmp)
        ICON_OPEN_FOLDER = iconImageList.Add(tmp)

        tmp = wx.Icon(os.path.join(iconDir, "array.ico"), wx.BITMAP_TYPE_ICO)
        icons.append(tmp)
        ICON_ARRAY = iconImageList.Add(tmp)

        iconDictionary = {TYPE_ARRAY: ICON_ARRAY,
                          TYPE_NO_DATA: ICON_UNAVAILABLE,
                          TYPE_RECORD: ICON_FOLDER}

        expandedIconDictionary = {TYPE_RECORD: ICON_OPEN_FOLDER}
