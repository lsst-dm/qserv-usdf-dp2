#!/usr/bin/env python3
  
import argparse
import json as json
import socket
import sys
import time

from ingest_api import ingest_api
from ingest_util import fatal, info, argument_parser, parse_contrib_location

def parseArguments():
    parser = argument_parser(
        """Start a transaction. Allocate chunks for the given contributions. Initiate ingestion
        of the contributions using ASYNC method. Wait before the completion of the operation.
        Commit the transaction.""")
    parser.add_argument(
        "--database",
        """The required name of a database.
        The database should exist and it should not be published.""")
    parser.add_argument(
        "--table",
        """The required name of a table where the contributions will be ingsted.
        The table should exist and it should not be published.""")
    parser.add_argument(
        "--fields-terminated-by",
        "Field separator that matches the CSV dialect of the contributions.",
        "\\t")
    parser.add_argument(
        "--fields-enclosed-by",
        """The optional character for quoting the fields. It should match the CSV dialect
        of the contributions.""",
        "")
    parser.add_argument(
        "urls",
        """The name of a plain text file with the URLs of the contributions.
        The file should have one URL per line.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")
    if args.fields_terminated_by is None or args.fields_terminated_by == "":
        fatal("The field terminator is required.")
    if args.urls is None or args.urls == "":
        fatal("The filename with a collection of contributions is required.")

    return args

host2ip = {}

def translate_host2ip(host):
    if host not in host2ip:
        while True:
            try:
                host2ip[host] = socket.gethostbyname(host)
                break
            except:
                pass

    return host2ip[host]


def get_chunk_locations(api, database, urls):
    chunks = set([parse_contrib_location(contrib_loc_str)["chunk"] for contrib_loc_str in urls])
    return api.locate_chunks(database, chunks)

if __name__ == '__main__':

    args = parseArguments()

    urls = []
    with open(args.urls, "r") as f:
        urls = [url[:-1] for url in f]

    api = ingest_api(args.qserv_config, args.debug)
    chunk_locations = get_chunk_locations(api, args.database, urls)
    trans_id = api.start_trans(args.database)
    if args.verbose:
        info("TRANS:     {}\tSTARTED".format(trans_id))

    contrib_entries = {}
    for contrib_loc_str in urls:
        contrib_loc = parse_contrib_location(contrib_loc_str)
        chunk   = contrib_loc["chunk"]
        overlap = contrib_loc["overlap"]
        url     = contrib_loc["url"]
        contrib_descr = {
            "transaction_id":       trans_id,
            "table":                args.table,
            "fields_terminated_by": args.fields_terminated_by,
            "fields_enclosed_by":   args.fields_enclosed_by,
            "chunk":                chunk,
            "overlap":              overlap,
            "url":                  url}
        location = chunk_locations[chunk]
        location["http_addr"] = translate_host2ip(location["http_host_name"])
        contrib = api.async_contrib(location, contrib_descr)
        contrib_id = contrib["id"]
        contrib_entries[contrib_id] = {
            "location": location,
            "contrib": contrib,
        };
        if args.verbose:
            info("CONTRIB:   {}\t{}\tworker={}".format(contrib_id, contrib["status"], location["worker"]))

    failed_contrib_entries = {}

    while len(contrib_entries) != 0:
        for contrib_id in list(contrib_entries.keys()):
            contrib = api.async_contrib_status(contrib_entries[contrib_id]["location"], contrib_id)
            contrib_entries[contrib_id]["contrib"] = contrib
            status = contrib["status"]
            if status == "IN_PROGRESS":
                entry = contrib_entries[contrib_id]
            else:
                entry = contrib_entries.pop(contrib_id)
                if status != "FINISHED":
                    failed_contrib_entries[contrib_id] = entry
            if args.verbose:
                info("CONTRIB:   {}\t{}\tworker={}".format(contrib_id, status, entry["location"]["worker"]))
        time.sleep(1)

    num_failed_contrib = len(failed_contrib_entries)
    if num_failed_contrib != 0:
        api.abort_trans(trans_id)
        if args.verbose:
            info("TRANS:     {}\tABORTED".format(trans_id))
        fatal("failed_contribs={}".format([contrib_id for contrib_id in failed_contrib_entries.keys()]))
    else:
        api.commit_trans(trans_id)
        if args.verbose:
            info("TRANS:     {}\tCOMMITTED".format(trans_id))

