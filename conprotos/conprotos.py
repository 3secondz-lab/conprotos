import argparse
import os

import pandas as pd
import pyarrow.parquet as pq
import utils

logger = utils.logger


class ConProtos:

    _options = utils.DEFAULT_OPTIONS

    def __init__(self, src: str | None = None, format: str | None = None):
        if not src and not format:
            return

        if not src:
            src = os.path.join(os.getcwd(), src)
            if not os.path.isfile(src):
                logger.error("File not exist")
                raise FileNotFoundError(f"{src}")

        if not format:
            _, format = os.path.splittext(src)
            for fmt, ext in utils.EXTENTION_MAP.items():
                if format.lower() in ext:
                    format = fmt
                    break

        if not format or not format.lower() in utils.SUPPORTED_FORMATS:
            logger.error(f"Unsupported file format: {format}")
            raise RuntimeError(f"{src}")

        self.read = utils.FTypes.get_reader(format)
        self.write = utils.FTypes.get_writer(format)
