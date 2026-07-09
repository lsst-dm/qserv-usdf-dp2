#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Alter table schema accoding to the desired specification")
    parser.add_argument(
        "spec",
        "The required specification in the ALTER TABLE statement to be applied for the table.")
    parser.add_argument(
        "--database",
        """The required name of a database where the table will be registered.
        The database should exist and it should be published.""")
    parser.add_argument(
        "--table",
        """The required name of a table affected by the operation.
        The table should not exist.""")

    args = parser.parse_args()
    if args.spec == "":
        fatal("The specification can't be empty.")
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':
    args = parseArguments()
    api = ingest_api(args.qserv_config, args.debug)
    api.alter_table(args.database, args.table, args.spec)

