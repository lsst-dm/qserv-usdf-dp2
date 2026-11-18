#!/usr/bin/env python3

import argparse
import json as json
import sys

from ingest_api import ingest_api
from ingest_util import fatal, argument_parser

def parseArguments():
    parser = argument_parser(
        "Change a password of the specified MySQl user")
    parser.add_argument(
        "--mysql-root-password",
        """The password of the MySQL root user.""")
    parser.add_argument(
        "user",
        "The name of the MySQL user affected by the change.")
    parser.add_argument(
        "host",
        "The name of a host which will be authorized to connect to the MySQL service.")
    parser.add_argument(
        "password",
        "The new password to be set for the user.")

    args = parser.parse_args()
    if args.mysql_root_password is None or args.mysql_root_password == "":
        fatal("The argument mysql-root-password is required.")
    if args.user == "":
        fatal("The user name can't be empty.")
    if args.host == "":
        fatal("The host name can't be empty.")

    return args

if __name__ == '__main__':
    args = parseArguments()
    api = ingest_api(args.qserv_config, args.debug)

    config = api._get_repl_config()
    for worker_def in config["config"]["workers"]:
        worker = worker_def["name"]
        api.set_mysql_password(args.mysql_root_password, worker, args.user, args.host, args.password)
