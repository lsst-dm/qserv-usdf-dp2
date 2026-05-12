#!/usr/bin/env python3
  
import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Compute or update row counters on the specified table.")
    parser.add_argument(
        "--database",
        """The required name of a database.
        The database should exist, and it can be published or not.""")
    parser.add_argument(
        "--table",
        """The required name of the table affected y the operation.
        The table should exist and it can be published or not.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    overlap_selector = "CHUNK_AND_OVERLAP"
    row_counters_state_update_policy = "ENABLED"
    row_counters_deploy_at_qserv = True
    force_rescan = True

    api = ingest_api(args.qserv_config, args.debug)
    api.rebuild_row_counters(
        args.database,
        args.table,
        overlap_selector,
        row_counters_state_update_policy,
        row_counters_deploy_at_qserv,
        force_rescan)

