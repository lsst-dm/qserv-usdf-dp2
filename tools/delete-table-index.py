#!/usr/bin/env python3
  
import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Delete table index on the specified table in a scope of a database")
    parser.add_argument(
        "index",
        "The name of an existing index to be deleted.")
    parser.add_argument_bool(
        "--overlap",
        "Delete the index in the overlap table")
    parser.add_argument(
        "--database",
        """The required name of a database where the table will be registered.
        The database should exist and it should be published.""")
    parser.add_argument(
        "--table",
        """The required name of a table where the index will be created.
        The table should exist and it should be published.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.delete_table_index(args.database, args.table, args.index, 1 if args.overlap else 0)

