#!/usr/bin/env python
# -*- encoding=utf8 -*-
from log import logger


class AsstException(Exception):

    def __init__(self, message):
        super().__init__(message)
        logger.error(message)
