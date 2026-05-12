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

def get_chunk_location(api, database, chunk):
    chunks = set([chunk,])
    locations = api.locate_chunks(database, chunks)
    if chunk not in locations:
        fatal("Incorect location reported for chunk={}".format(chunk))
    return locations[chunk]

if __name__ == '__main__':

    args = parseArguments()

    api = ingest_api(args.qserv_config, args.debug)

    chunk = contrib2chunk(args.url)
    chunk_location = get_chunk_location(api, args.database, chunk)

    trans_id = api.start_trans(args.database)

    contrib_descr = {
        "transaction_id":       trans_id,
        "table":                args.table,
        "fields_terminated_by": args.fields_terminated_by,
        "fields_enclosed_by":   args.fields_enclosed_by,
        "chunk":                chunk,
        "overlap":              contrib2overlap(args.url),
        "url":                  args.url}

    contrib = api.async_contrib(chunk_location, contrib_descr)
    if args.verbose:
        info("CONTRIB:   {}\t{}\t{}".format(contrib["id"], contrib["status"], chunk_location["worker"]))
    while contrib["status"] == "IN_PROGRESS":
        time.sleep(1)
        contrib = api.async_contrib_status(chunk_location, contrib["id"])
        if args.verbose:
             info("CONTRIB:   {}\t{}\t{}".format(contrib["id"], contrib["status"], chunk_location["worker"]))

    if contrib["status"] == "FINISHED":
        api.commit_trans(trans_id)
    else:
        api.abort_trans(trans_id)
        fatal("CONTRIB:   {}\t{}\t{}\t{}".format(contrib["id"], contrib["status"], chunk_location["worker"], contrib["error"]))

