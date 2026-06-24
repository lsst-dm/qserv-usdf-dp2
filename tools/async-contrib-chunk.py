#!/usr/bin/env python3
  
import argparse
import json as json
import sys
import time

from ingest_api import ingest_api
from ingest_util import fatal, info, argument_parser, contrib2chunk, contrib2overlap

def parseArguments():
    parser = argument_parser(
        """Start a transaction. Allocate a chunk. Initiate ingestion of the chunk
        contribution using ASYNC method. Wait before the completion of the operation.
        Commit the transaction.""")
    parser.add_argument(
        "--database",
        """The required name of a database.
        The database should exist and it should not be published.""")
    parser.add_argument(
        "--table",
        """The required name of a table where the contributions will be ingsted.
        The table should exist and it should not be published.""")
    parser.add_argument_bool(
        "--all-replicas",
        "Ingest contributions into all replicas")
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
        "--url",
        """A location of the contribution. The chunk number and the overal attribute will
        be deduced from the name of the file.""")

    args = parser.parse_args()
    if args.database is None or args.database == "":
        fatal("The database name is required.")
    if args.table is None or args.table == "":
        fatal("The table name is required.")
    if args.fields_terminated_by is None or args.fields_terminated_by == "":
        fatal("The field terminator is required.")
    if args.url is None or args.url == "":
        fatal("The URL of the contribution is required.")

    return args

def get_chunk_locations(api, database, all_replicas, chunk):
    chunks = set([chunk,])
    locations = api.locate_chunks(database, chunks, all_replicas)
    if chunk not in locations:
        fatal("Incorect location reported for chunk={}".format(chunk))
    return locations[chunk]

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)

    chunk = contrib2chunk(args.url)
    chunk_locations = get_chunk_locations(api, args.database, args.all_replicas, chunk)

    trans_id = api.start_trans(args.database)
    contrib_entries = []
    for location in chunk_locations:
        contrib_descr = {
            "transaction_id":       trans_id,
            "table":                args.table,
            "fields_terminated_by": args.fields_terminated_by,
            "fields_enclosed_by":   args.fields_enclosed_by,
            "chunk":                chunk,
            "overlap":              contrib2overlap(args.url),
            "url":                  args.url}

        contrib = api.async_contrib(location, contrib_descr)
        contrib_entries.append({
            "contrib":  contrib,
            "location": location
        })
        if args.verbose:
            info("CONTRIB:   {}\t{}\t{}".format(contrib["id"], contrib["status"], location["worker"]))

    # Track contributions until all finish or fail
    num_failed = 0
    while True:
        num_in_progress = 0
        num_failed = 0
        for entry in contrib_entries:
            if entry["contrib"]["status"] == "IN_PROGRESS":
                num_in_progress = num_in_progress + 1
                time.sleep(1)
                entry["contrib"] = api.async_contrib_status(entry["location"], entry["contrib"]["id"])
                if args.verbose:
                    info("CONTRIB:   {}\t{}\t{}".format(entry["contrib"]["id"], entry["contrib"]["status"], entry["location"]["worker"]))
            elif entry["contrib"]["status"] == "FINISHED":
                if args.verbose:
                    info("CONTRIB:   {}\t{}\t{}".format(entry["contrib"]["id"], entry["contrib"]["status"], entry["location"]["worker"]))
            else:
                num_failed = num_failed + 1
                if args.verbose:
                    info("CONTRIB:   {}\t{}\t{}\t{}".format(entry["contrib"]["id"], entry["contrib"]["status"], entry["location"]["worker"], entry["contrib"]["error"]))
        if num_in_progress == 0:
            break

    # Finish or abort the transaction 
    if num_failed == 0:
        api.commit_trans(trans_id)
    else:
        api.abort_trans(trans_id)
        fatal("TRANS:     ABORTED trans_id={} num_failed_contribs={}".format(trans_id, num_failed,))

