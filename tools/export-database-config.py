#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        """Export a configuration of a database into the output text file.
        The file will contain the JSON-formatted specification of the database. The JSON schema
        of the specification will be compatible with the schema expected by the database registration service.
        Note that the JSON object won't have the attribute `auth_key`.""")
    parser.add_argument(
        "config",
        """The name of the plain text file where to write the JSON-formatted specification.""")
    parser.add_argument(
        "--database",
        """The required name of a database. The database must be in the 'published' state.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")

    return args

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)
    config_json = api.export_database_config(args.database)

    with open(args.config, "w") as f:
        f.write(json.dumps(config_json["config"], indent=2))
