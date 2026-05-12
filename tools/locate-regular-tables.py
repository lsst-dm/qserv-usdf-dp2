#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Locate regular tables")
    parser.add_argument(
        "--database",
        """The required name of a database where to locate tables.
        The database should exist.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    locations = api.locate_regular_tables(args.database)

    for loc in locations:
        print(loc)

