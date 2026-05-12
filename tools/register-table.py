#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Register the specified table in a scope of a database")
    parser.add_argument(
        "config",
        "The name of the JSON-formatted file with a configuration of the table.")
    parser.add_argument(
        "--database",
        """The required name of a database where the table will be registered.
        The database should exist and it should be unpublished.""")
    parser.add_argument(
        "--table",
        """The required name of a table to be registered.
        The table should not exist.""")
    parser.add_argument(
        "--charset",
        """The optional name of the desired character set for the table. If it's
        provided then the character set specified (if any) in the configuration
        file's attribute 'charset_name' will be sent with the table creation request.
        If the option is not used and the file has no atribute or if the attribute
        is empty in both then the server default will be assumed.""",
        None)
    parser.add_argument(
        "--collation",
        """The optional name of the desired collation for the table. If it's
        provided then the collation specified (if any) in the configuration
        file's attribute 'collation_name' will be sent with the table creation request.
        If the option is not used and the file has no atribute or if the attribute
        is empty in both then the server default will be assumed.""",
        None)

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    with open(args.config, "r") as f:
        table_config = json.loads(f.read())

    api = ingest_api(args.qserv_config, args.debug)
    api.register_table(args.database, args.table, table_config, args.charset, args.collation)

