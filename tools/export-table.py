#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        """Export table location into the output text file. There will be only one URL in the file.""")
    parser.add_argument(
        "urls",
        """The name of the plain text file where the table location will be recorded.""")
    parser.add_argument(
        "--database",
        """The required name of a database where the exported chunks are located.
        The database should exist.""")
    parser.add_argument(
        "--table",
        """The required name of a table where the exported chunks are located.
        The table should exist.""")
    parser.add_argument(
        "--fields-terminated-by",
        """The CSV dialect option. The default value is comma.""")
    parser.add_argument(
        "--fields-enclosed-by",
        """The CSV dialect option. By default, fields are not enclosed.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    locations = api.export_table(args.database, args.table, args.fields_terminated_by, args.fields_enclosed_by)

    with open(args.urls, "w") as f:
        for loc in locations:
            f.write("{}\n".format(loc))
