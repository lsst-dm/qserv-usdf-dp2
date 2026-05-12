#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Register/located chunks")
    parser.add_argument(
        "chunks",
        """The name of the plain textfile with a collection of chunk numbers.
        Each chunk must be placed on a separate line""")
    parser.add_argument(
        "--database",
        """The required name of a database where to register/locate chunks.
        The database should exist.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    chunks = set()
    with open(args.chunks, "r") as f:
        for line in f:
            chunks.add(int(line))

    api = ingest_api(args.qserv_config, args.debug)
    locations = api.locate_chunks(args.database, chunks)

    for chunk,loc in locations.items():
        print(loc)

