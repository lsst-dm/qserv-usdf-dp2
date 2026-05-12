#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Set or change the scan rating of the specified table in a scope of a database")
    parser.add_argument(
        "rating",
        "The required parameter with the rating (the positive number) to be set for the table.")
    parser.add_argument(
        "--database",
        """The required name of a database where the table is residing.
        The database should exist and it should be published.""")
    parser.add_argument(
        "--table",
        """The required name of a table affected by the operation.
        The table should exist.""")

    args = parser.parse_args()
    if args.rating == "":
        fatal("The rating can't be empty.")
    try:
        args.rating = int(args.rating)
    except:
        fatal("The rating is not a number.")
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':
    args = parseArguments()
    api = ingest_api(args.qserv_config, args.debug)
    api.set_scan_rating(args.database, args.table, args.rating)

