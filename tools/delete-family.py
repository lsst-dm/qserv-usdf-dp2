#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser 

def parseArguments():
    parser = argument_parser(
        "Delete the specified database family")
    parser.add_argument(
        "--family",
        """The required name of a database family to be deleted.
        The family should exist.""")
    parser.add_argument_bool(
        "--force",
        "Proceed with the removal even of the family is not empty (has databases)")

    args = parser.parse_args()
    if args.family is None or args.family == "":
        fatal("The database family name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.delete_family(args.family, args.force)

