#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Delete the specified table")
    parser.add_argument(
        "--database",
        """The required name of a database where the table to be deleted resides.
        The database should exist.""")
    parser.add_argument(
        "--table",
        """The required name of a table to be deleted. The table should exist.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.delete_table(args.database, args.table)

