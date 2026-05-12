#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Set configuration parameters of the ingest in a scope of the specified database")
    parser.add_argument(
        "config",
        "The name of the JSON-formatted file with a collection of the configuration parameters for the database")
    parser.add_argument(
        "--database",
        """The required name of a database where to ingest the contributions.
        The database should not exist.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    with open(args.config, "r") as f:
        ingest_config = json.loads(f.read())

    api = ingest_api(args.qserv_config, args.debug)
    api.set_ingest_config(args.database, ingest_config)

