#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser 

def parseArguments():
    parser = argument_parser(
        "Delete the specified database")
    parser.add_argument(
        "--database",
        """The required name of a database to be deleted.
        The database should exist.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.delete_database(args.database)

