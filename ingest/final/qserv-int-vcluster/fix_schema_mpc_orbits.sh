#!/bin/bash

function TIMESTAMP {
  echo "[$(date +'%F %H:%M:%S')] "
}

BASE_DIR=$(dirname "$0")
if [ -z "$BASE_DIR" ] || [ "$0" = "bash" ]; then
    >&2 echo "error: variable 'BASE_DIR' is not defined";
    return 1;
fi
BASE_DIR=$(readlink -e "$BASE_DIR")
if [ ! -d "$BASE_DIR" ]; then
    >&2 echo "error: path 'BASE_DIR' is not a valid directory";
    return 1;
fi
LOG_DIR=${BASE_DIR}/logs
cd ${BASE_DIR}

rm -rf ${LOG_DIR}
mkdir -p ${LOG_DIR}

TOOLS=${BASE_DIR}/../../../tools

# Variables that define a scope of the ingest
DATABASE=dp2
DATABASE_OPT="--database=${DATABASE}"
VERBOSE_OPT="--verbose"
DEBUG_OPT=

# NOTE: Kubernetes-based deployments only!
# Prepare the confguration file qserv.json. The file will contain the authorization
# context for the subsequent operations performed by the ingest tools.
source make_config.source

APP=alter-table
TABLE=mpc_orbits
ALTER_SPEC='ADD COLUMN designation VARCHAR(255) GENERATED ALWAYS AS (unpacked_primary_provisional_designation) AFTER unpacked_primary_provisional_designation'
LOG=${LOG_DIR}/${APP}-${TABLE}.log
echo $(TIMESTAMP)"Fixing table schema ${TABLE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} "${ALTER_SPEC}" ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

echo $(TIMESTAMP)DONE

