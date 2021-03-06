import copy
import logging
import traceback

import pandas

logger = logging.getLogger("conprotos")
formatter = logging.Formatter(
    fmt="{asctime} - {name:10s} [{levelname:^7s}] {message}",
    style="{",
    datefmt="%m/%d/%Y %H:%M:%S",
)
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)

EXTENTION_MAP = {
    "hdf": [".hdf", ".h4", ".h5", ".hdf4", ".hdf5"],
    "parquet": [".parquet", ".pq"],
    "csv": [".csv"],
    "feather": [".feather"],
    "pickle": [".p", ".pk", ".pkl"],
    "json": [".json"],
}

SUPPORTED_FORMATS = ["hdf", "parquet", "csv", "feather", "pickle", "json"]

DEFAULT_OPTIONS = {"protobuf_syntax": 3, "protobuf_ignore_nan": True}


class FTypes:
    @classmethod
    def get_reader(cls, arg):
        _reader_type = "reader_" + str(arg).lower()
        _reader = getattr(cls, _reader_type, lambda: "defualt")
        return _reader

    @classmethod
    def get_writer(cls, arg):
        _writer_type = "reader_" + str(arg).lower()
        _writer = getattr(cls, _writer_type, lambda: "defualt")
        return _writer

    def reader_hdf(self):
        return pandas.read_csv

    def reader_parquet(self):
        return pandas.read_parquet

    def reader_csv(self):
        return pandas.read_csv

    def reader_feather(self):
        return pandas.read_feather

    def reader_pickle(self):
        return pandas.read_pickle

    def reader_json(self):
        return pandas.read_json

    def writer_hdf(self):
        return pandas.to_hdf

    def writer_parquet(self):
        return pandas.to_parquet

    def writer_csv(self):
        return pandas.to_csv

    def writer_feather(self):
        return pandas.to_feather

    def writer_pickle(self):
        return pandas.to_pickle

    def writer_json(self):
        return pandas.to_json


class ProtoMessage:
    def __init__(self, level: int = 0, message_name: str | None = None, parent=None):

        # For script
        if message_name is None:
            (_, _, _, _text) = traceback.extract_stack()[-2]
            message_name = _text[: _text.find("=")].strip()

        # For interpreter
        if not message_name:
            raise AttributeError(
                "Message name should be specified manually in interpreter environment - ProtoMessage(message_name='NAME')"
            )

        self.__name = message_name
        self.__level = level
        self.__childs = []
        self.__fields = []
        if parent:
            self.__parent = parent
            if self.__level is not self.parent.level:
                self.__level = self.parent.level + 1
            logger.info(
                "Submessage '{self.__name}' added to message '{self.__parent.name}'"
            )
        else:
            self.__parent = None

    @property
    def name(self):
        return self.__name

    @property
    def level(self):
        return self.__level

    @property
    def parent(self):
        return self.__parent

    @property
    def childs(self):
        return self.__childs

    @property
    def fields(self):
        return self.__fields

    @level.setter
    def level(self, _level):
        if self.parent and _level is not self.parent.level + 1:
            logger.error(
                f"Indent level of submessage must be greater than parent message level"
            )
            raise ValueError(
                f"Indent level of {self.name} must be {self.parent.level+1}"
            )

        self.__level = _level

        if self.childs:
            for child in self.childs:
                child.level = self.level + 1

    @parent.setter
    def parent(self, _parent):
        if not _parent:
            logger.warning(
                "Remove parent message will be adjust current message's level to 0"
            )
            self.__parent = None
            self.level = 0
        else:
            if _parent.level and not _parent.parent:
                logger.info(
                    f"Parent message '{_parent.name}' does not have top indent level {_parent.level}"
                )
            self.__parent = _parent
            self.level = self.parent.level + 1

    @parent.deleter
    def parent(self):
        self.__parent = None

    @childs.setter
    def childs(self, _child):
        if _child.level is not self.level + 1:
            logger.info(
                f"Indent level of '{_child.name}' has been adjusted to {self.level + 1}"
            )
        if _child.parent:
            if _child.parent is not self:
                logger.info(
                    f"Message '{_child.name}' already has a parent '{_child.parent.name}'"
                )
                logger.info(
                    f"A copy of child message '{_child.name}' added to current message '{self.name}'"
                )
                self.__childs.append(copy.deepcopy(_child))
        else:
            self.__childs.append(_child)
        self.__childs[-1].level = self.level + 1
        self.__childs[-1].parent = self

    @childs.deleter
    def childs(self, _child=None):
        if _child:
            if _child in self.__childs:
                self.__childs.remove(_child)
            else:
                raise KeyError(f"Child '{_child.name}' is not in '{self.name}'")

        else:
            self.__childs = []

    @staticmethod
    def header_string(_version: str | None = None):
        _out_string = "# Autogenerated Message Schema from ConProtos\n"
        _out_string += "# Author : Yoonjin Hwang\n"
        _out_string += "# Repository : github.com/3secondz-lab/conprotos\n\n"
        _out_string += f"# ConProtos __Version__ {_version}"

        return _out_string

    @staticmethod
    def syntax_string(_version: int = 3):
        if _version not in [2, 3]:
            logger.warning("Version is not specified: Use Default '3'")
            _version = 3

        if _version == 2:
            logger.error(
                "Proto 2 Syntax is not supported currently. Use Proto 3 Syntax"
            )
            _version = 3

        _out_string = 'syntax = "proto'
        _out_string = f'{_version}"\n\n'

        return _out_string

    @staticmethod
    def message_string(
        _name: str, _message_dict: dict, _start_index: int = 0, _add_indent: int = 0
    ):
        _out_string = []
        _out_string[0] = "message " + _name + " {"
        for key in _message_dict.keys():
            _type_guess = set(map(type, _message_dict[key]))
            _start_index += 1
            if not len(_type_guess) == 1:
                logger.warning(
                    f"Non-homogeneous variable type with key : {key} {_type_guess}"
                )
                logger.warning(
                    f"This item will be ignored with reserved item number : {_start_index}"
                )
                continue

    @staticmethod
    def get_type(cls, var):
        if type(var) is dict:
            return "message"
        elif type(var) is list:
            return
