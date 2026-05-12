import argparse
from datetime import datetime
now = datetime.now()
import json as json
import sys

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def info(msg):
    sys.stdout.write("{}  {}\n".format(timestamp(), msg))
    sys.stdout.flush()

def fatal(msg):
    sys.stderr.write("{}  {}\n".format(timestamp(), msg))
    sys.stderr.flush()
    sys.exit(1)

class argument_parser:

    def __init__(self, descr):
        self._argparse = argparse.ArgumentParser(descr)
        self._argparse.add_argument(
            "--qserv",
            help="""The name of the required JSON-formatted configuration file for Qserv.
            The file should containe a unique identifier of the Qserv instance, the base URL for
            connecting to the Replication Controller, and the authorization keys.""",
            default="qserv.json")
        self._argparse.add_argument(
            "-v", "--verbose",
            action="store_true")
        self._argparse.add_argument(
            "-d", "--debug",
            action="store_true")

    def add_argument(self, name, help="", default=None):
        self._argparse.add_argument(name, help=help, default=default)

    def add_argument_bool(self, name, help=""):
        self._argparse.add_argument(name, help=help, action="store_true")

    def parse_args(self):
        self._args = self._argparse.parse_args()
        self._args.qserv_config = self._parse_qserv_config()
        return self._args

    def _parse_qserv_config(self):
        if self._args.qserv == "":
            fatal("The configuration file for Qserv is required.")
        with open(self._args.qserv, "r") as f:
            config = json.loads(f.read())
            for key in ("instance-id", "repl-contr-url", "auth-key", "admin-auth-key"):
                if key not in config:
                    fatal("required key '{}' was not found in the Qserv configuration".format(key))
            return config

def contrib2chunk(url):
    fname = url.split("/")[-1][0:-4][6:]
    if len(fname) > len("_overlap") and "_overlap" == fname[-8:]:
        return int(fname[0:-8])
    else:
        return int(fname)

def contrib2overlap(url):
    fname = url.split("/")[-1][0:-4][6:]
    if len(fname) > len("_overlap") and "_overlap" == fname[-8:]:
        return 1
    else:
        return 0

def urls2chunks(filename):
    chunks = set()
    with open(filename, "r") as f:
        for url in f:
            chunks.add(contrib2chunk(url))
    return chunks

def parse_contrib_location(loc):

    # Location strings may have one of the following formats
    #
    # - Direct URLs to the CVS files of chunks or chunk overlaps:
    #
    #     http://<host>:<port>/.../chunk_<number>.txt
    #     http://<host>:<port>/.../chunk_<number>_overlap.txt
    #     https://<host>:<port>/.../chunk_<number>.txt
    #     https://<host>:<port>/.../chunk_<number>_overlap.txt
    #
    #   Note that the last fragment of the path is required to have
    #   a special format illustrated above. The algorithm of the function
    #   relies on ti sconvention to extract the chunk number and the overlap
    #   attribute from the url.
    #
    # - Serialized JSON objects:
    #
    #     {"chunk":<number>,"overlap":<number>,"url":<string>}
    #
    #   Where a value of the "url" attribute could be any valid location.
    #   No specific naming convention exists for these urls.
    #
    # The method returns a dictionary that's is similar to the schema of
    # the serialized JSON object.

    if loc.startswith("http"):
        return {
            "chunk": contrib2chunk(loc),
            "overlap": contrib2overlap(loc),
            "url": loc}

    return json.loads(loc)
