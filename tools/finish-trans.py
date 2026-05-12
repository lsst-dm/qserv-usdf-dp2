#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Commit or abort the specified transaction")
    parser.add_argument(
        "trans",
        """The unique identifier of a transaction affected by the operation.
        The transaction should be open.""")
    parser.add_argument_bool(
        "--abort",
        "Abort the transaction")

    args = parser.parse_args()
    if args.trans is None or args.trans == "":
        fatal("Incorrect transactiion identifier.")
    args.trans_id = int(args.trans)

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    if args.abort:
        api.abort_trans(args.trans_id)
    else:
        api.commit_trans(args.trans_id)
