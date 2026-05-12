#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Set the desired replication level at the specified database family")
    parser.add_argument(
        "--family",
        """The required name of a database family affected by the operation.
        The database should exist, it can be published or not.""")
    parser.add_argument(
        "level",
        """The required replicaton level for the family. The number must be at least 1.
        The level may be also limited by this application to avoid damaging Qserv deployment.""")

    args = parser.parse_args()
    if args.family is None or args.family == "":
        fatal("The database family name is required.")
    if args.level is None or args.level == "":
        fatal("The replication level is required.")

    args.level = int(args.level)
    if args.level < 1 or args.level > 3:
        fatal("The replication level must be in a range of [1,3]")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    api.set_repl_level(args.family, args.level)

