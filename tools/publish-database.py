#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Publish the specified database")
    parser.add_argument(
        "--database",
        """The required name of a database affected by the operation.
        The database should exist, it should not be published, and it should
        not have anynfinished transactions.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.publish_database(args.database)

