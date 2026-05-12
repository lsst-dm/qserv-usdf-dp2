import json as json
import random
import requests
import sys

def _info(message):
    sys.stdout.write("{}\n".format(message))
    sys.stdout.flush()

def _error(method, url, code, message):
    sys.stderr.write("[ERROR]    method={} url={} http_code={} server_error={}\n".format(method, url, code, message))
    sys.stdout.flush()

def _fatal(method, url, code, message):
    _error(method, url, code, message)
    sys.exit(1)

class ingest_api:

    def __init__(self, qserv_config, debug=False):
        self._qserv_config = qserv_config
        self._debug = debug

    def delete_family(self, family, force=False):
        if self._debug:
            _info("DELETE:    family={} force={}".format(family, int(force)))

        data = {}
        url = "{}/replication/config/family/{}?force={}".format(self._qserv_config["repl-contr-url"], family, int(force))

        self._delete(url, data)

    def register_database(self, database, data):
        if self._debug:
            _info("REGISTER:  database={}".format(database))

        data["database"] = database
        url = "{}/ingest/database".format(self._qserv_config["repl-contr-url"])

        self._post(url, data)

    def delete_database(self, database):
        if self._debug:
            _info("DELETE:    database={}".format(database))

        data = {}
        url = "{}/ingest/database/{}".format(self._qserv_config["repl-contr-url"], database)

        self._delete(url, data)

    def publish_database(self, database):
        if self._debug:
            _info("PUBLISH:   database={}".format(database))

        data = {}
        url = "{}/ingest/database/{}".format(self._qserv_config["repl-contr-url"], database)

        self._put(url, data)

    def unpublish_database(self, database):
        if self._debug:
            _info("UNPUBLISH: database={}".format(database))

        data = {}
        url = "{}/replication/config/database/{}".format(self._qserv_config["repl-contr-url"], database)

        self._put(url, data)

    def set_ingest_config(self, database, data):
        url = "{}/ingest/config".format(self._qserv_config["repl-contr-url"])
        data["database"] = database
        self._put(url, data)

    def register_table(self, database, table, data, charset=None, collation=None):
        if self._debug:
            _info("REGISTER:  database={} table={}".format(database, table))

        data["database"] = database
        data["table"] = table

        # The charset or collation names are allowed in the REST API as the versaion 49.
        # The server must support these.
        if charset   is not None: data["charset_name"]   = charset
        if collation is not None: data["collation_name"] = collation
        if "charset_name" in data or "collation_name" in data:
            data["version"] = 49

        url = "{}/ingest/table".format(self._qserv_config["repl-contr-url"])

        self._post(url, data)

    def delete_table(self, database, table):
        if self._debug:
            _info("DELETE:    database={} table={}".format(database, table))

        data = {}
        url = "{}/ingest/table/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)

        self._delete(url, data)

    def locate_chunks(self, database, chunks):
        if self._debug:
            _info("LOCATE:    database={} chunks={}".format(database, chunks))

        data = {
            "database": database,
            "chunks":   [chunk for chunk in chunks],
        }
        url = "{}/ingest/chunks".format(self._qserv_config["repl-contr-url"])

        respJson = self._post(url, data)

        # There was a change in REST API 52, in whichthe names of the location keys
        # were unified to be "locations". The fix was meant to address inconsisttencies
        # in the REST API. The iterator below tries both keys to see which one would work:
        locations = {}
        key = "location" if "location" in respJson else "locations"
        for location in respJson[key]:
            locations[location["chunk"]] = location

        return locations

    def locate_regular_tables(self, database):
        if self._debug:
            _info("LOCATE:    database={}".format(database))

        data = {
            "database": database,
        }
        url = "{}/ingest/regular".format(self._qserv_config["repl-contr-url"])

        respJson = self._get(url, data)

        return respJson["locations"]

    def export_database_config(self, database):
        if self._debug:
            _info("EXPORT-C:  database={}".format(database))

        url = "{}/export/config/{}".format(self._qserv_config["repl-contr-url"], database)
        return self._get(url)

    def export_table_config(self, database, table):
        if self._debug:
            _info("EXPORT-C:  database={} table={}".format(database, table))

        url = "{}/export/config/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)
        return self._get(url)

    def export_chunks(self, database, table, is_director, fields_terminated_by, fields_enclosed_by):
        if self._debug:
            _info("EXPORT:    database={} table={} is_director{} fields_terminated_by={} fields_enclosed_by={}".format(
                database, table, is_director, fields_terminated_by, fields_enclosed_by))

        url = "{}/export/locations/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)
        respJson = self._get(url)

        locations = []
        for chunk_spec in respJson["chunks"]:
            chunk = chunk_spec["chunk"]
            if chunk == 1234567890:
                # The special chunk is never ingested directly
                continue

            # Pick the randon worker (if more than 1 is available) to ensure uniform
            # distribution of the chunk exportation requests among the workers.
            num_workers = len(chunk_spec["locations"])
            worker_idx = random.randint(0, num_workers-1)
            idx = 0
            for worker in chunk_spec["locations"]:
                if idx != worker_idx:
                    idx = idx + 1
                    continue
                base_url = "http://{}:{}/worker/export/{}/{}/{}".format(
                        worker["host"]["name"],
                        worker["port"],
                        database,
                        table,
                        chunk)
                csv_dialect=""
                if fields_terminated_by is not None and fields_terminated_by != "":
                    csv_dialect = "{}&fields_terminated_by={}".format(csv_dialect,fields_terminated_by)
                if fields_enclosed_by is not None and fields_enclosed_by != "":
                    csv_dialect = "{}&fields_enclosed_by={}".format(csv_dialect,fields_enclosed_by)
                locations.append({
                    "chunk":chunk,
                    "overlap":0,
                    "url":"{}?overlap=0{}".format(base_url, csv_dialect)})
                if is_director:
                    locations.append({
                        "chunk":chunk,
                        "overlap":1,
                        "url":"{}?overlap=1{}".format(base_url, csv_dialect)})
                break

        return locations

    def export_table(self, database, table, fields_terminated_by, fields_enclosed_by):
        if self._debug:
            _info("EXPORT:    database={} table={} fields_terminated_by={} fields_enclosed_by={}".format(database, table, fields_terminated_by, fields_enclosed_by))

        url = "{}/export/locations/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)
        respJson = self._get(url)

        locations = []

        # Pick the randon worker (if more than 1 is available) to ensure uniform
        # distribution of the chunk exportation requests among the workers.
        num_workers = len(respJson["locations"])
        worker_idx = random.randint(0, num_workers-1)
        idx = 0
        for worker in respJson["locations"]:
            if idx != worker_idx:
                idx = idx + 1
                continue
            csv_dialect=""
            if fields_terminated_by is not None and fields_terminated_by != "":
                separator = "?" if csv_dialect == "" else "&"
                csv_dialect = "{}{}fields_terminated_by={}".format(csv_dialect, separator, fields_terminated_by)
            if fields_enclosed_by is not None and fields_enclosed_by != "":
                separator = "?" if csv_dialect == "" else "&"
                csv_dialect = "{}{}fields_enclosed_by={}".format(csv_dialect, separator, fields_enclosed_by)
            url = "http://{}:{}/worker/export/{}/{}{}".format(
                worker["host"]["name"],
                worker["port"],
                database,
                table,
                csv_dialect)
            locations.append(url)
            break

        return locations

    def start_trans(self, database):
        if self._debug:
            _info("TRANS:     starting transaction")

        url = "{}/ingest/trans".format(self._qserv_config["repl-contr-url"])
        data = {"database": database}

        respJson = self._post(url, data)
        trans_id = int(respJson["databases"][database]["transactions"][0]["id"])
        if self._debug:
            _info("TRANS:     started transaction id={}".format(trans_id))

        return trans_id

    def commit_trans(self, trans_id):
        self._finish_trans(trans_id, False)

    def abort_trans(self, trans_id):
        self._finish_trans(trans_id, True)

    def _finish_trans(self, trans_id, abort=False):
        if self._debug:
            _info("TRANS:     finishing transaction id={} abort={}".format(trans_id, int(abort)))

        url = "{}/ingest/trans/{}?abort={}".format(self._qserv_config["repl-contr-url"], trans_id, int(abort))
        data = {}

        self._put(url, data)
        if self._debug:
            _info("TRANS:     finished transaction id={}".format(trans_id))

        return trans_id

    def create_table_index(self, database, table, data, overlap):
        if self._debug:
            _info("INDEX:     database={} table={}".format(database, table))

        data["database"] = database
        data["table"] = table
        data["overlap"] = overlap
        url = "{}/replication/sql/index".format(self._qserv_config["repl-contr-url"])

        self._post(url, data)

    def delete_table_index(self, database, table, index, overlap):
        if self._debug:
            _info("INDEX:     database={} table={} index={}".format(database, table, index))

        data = {
            "database": database,
            "table": table,
            "overlap": overlap,
            "index" : index,
        }
        url = "{}/replication/sql/index".format(self._qserv_config["repl-contr-url"])

        self._delete(url, data)

    def create_director_index(self, database, table, rebuild=False):
        if self._debug:
            _info("DIR-INDEX: database={} table={}".format(database, table))

        data = {
            "database":       database,
            "director_table": table,
            "rebuild":        int(rebuild),
        }
        url = "{}/ingest/index/secondary".format(self._qserv_config["repl-contr-url"])

        self._post(url, data)

    def async_contrib(self, location, contrib_descr):
        if self._debug:
            #_info("CONTRIB:   worker={}:{} descr={}".format(location["http_host_name"], location["http_port"], contrib_descr))
            _info("CONTRIB:   worker={}:{} descr={}".format(location["http_addr"], location["http_port"], contrib_descr))

        # url = "http://{}:{}/ingest/file-async".format(location["http_host_name"], location["http_port"])
        url = "http://{}:{}/ingest/file-async".format(location["http_addr"], location["http_port"])
        return self._post(url, contrib_descr)["contrib"]

    def async_contrib_status(self, location, contrib_id):
        if self._debug:
            #_info("CONTRIB:   worker={}:{} id={}".format(location["http_host_name"], location["http_port"], contrib_id))
            _info("CONTRIB:   worker={}:{} id={}".format(location["http_addr"], location["http_port"], contrib_id))

        #url = "http://{}:{}/ingest/file-async/{}".format(location["http_host_name"], location["http_port"], contrib_id)
        url = "http://{}:{}/ingest/file-async/{}".format(location["http_addr"], location["http_port"], contrib_id)
        return self._get(url)["contrib"]

    def rebuild_row_counters(self,
                             database,
                             table,
                             overlap_selector,
                             row_counters_state_update_policy,
                             row_counters_deploy_at_qserv,
                             force_rescan):
        if self._debug:
            _info("COUNTERS:  database={} table={}".format(database, table))

        url = "{}/ingest/table-stats".format(self._qserv_config["repl-contr-url"])
        data = {
            "database": database,
            "table": table,
            "overlap_selector" : overlap_selector,
            "row_counters_state_update_policy": row_counters_state_update_policy,
            "row_counters_deploy_at_qserv": row_counters_deploy_at_qserv,
            "force_rescan": force_rescan,
        }
        return self._post(url, data)

    def set_repl_level(self, family, level):
        if self._debug:
            _info("REPL-LVL:  family={} level={}".format(family, level))

        url = "{}/replication/level".format(self._qserv_config["repl-contr-url"])
        data = {
            "family": family,
            "replication_level": level
        }
        return self._put(url, data)

    def alter_table_charset(self, database, table, charset, collation):
        if self._debug:
            _info("CHARSET:   database={} table={} charset={} collation={}".format(database, table, charset, collation))

        url = "{}/replication/sql/table/schema/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)
        data = {
            "spec": "CONVERT TO CHARACTER SET {} COLLATE {}".format(charset, collation),
        }
        return self._put(url, data)

    def set_scan_rating(self, database, table, rating):
        if self._debug:
            _info("SCAN:      database={} table={} rating={}".format(database, table, rating))

        url = "{}/replication/qserv/css/shared-scan/{}/{}".format(self._qserv_config["repl-contr-url"], database, table)
        data = {
            "scanRating": rating,
        }
        return self._put(url, data)

    def _get(self, url, data=None):
        return self._request("GET", url, data)

    def _post(self, url, data):
        return self._request("POST", url, data)

    def _put(self, url, data):
        return self._request("PUT", url, data)

    def _delete(self, url, data):
        return self._request("DELETE", url, data)

    def _request(self, method, url, data=None):
        if self._debug:
            _info("REQUEST:   method={} url={} data={}".format(method, url, data))

        if method == "GET":
            if "api_version" in self._qserv_config:
                query_param_separator = "?" if url.find("?") == -1 else "&"
                url = "{}{}version={}".format(url, query_param_separator, self._qserv_config["api_version"])
        else:
            data["auth_key"] = self._qserv_config["auth-key"]
            data["admin_auth_key"] = self._qserv_config["admin-auth-key"]
            if ("version" not in data) and ("api_version" in self._qserv_config):
                data["version"] = self._qserv_config["api_version"]

        resp = requests.request(method, url, json=data, timeout=None)
        if resp.status_code != 200:
            _fatal(method, url, resp.status_code, "") 

        respJson = resp.json()
        if not respJson["success"]:
            if self._debug:
                _fatal(method, url, resp.status_code, respJson["error"] + "error_ext:" + str(respJson["error_ext"]))
            else:
                _fatal(method, url, resp.status_code, respJson["error"])

        return respJson

