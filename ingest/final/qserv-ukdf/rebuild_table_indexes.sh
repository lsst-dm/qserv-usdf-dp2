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
INDEX_CONFIG=${BASE_DIR}/../indexes

# Variables that define a scope of the ingest
DATABASE=dp2
DATABASE_OPT="--database=${DATABASE}"
VERBOSE_OPT="--verbose"
DEBUG_OPT="--debug"
PARTITIONED_TABLES="Object Source ForcedSource DiaObject DiaSource DiaSourceOnDiaObject DiaSourceOnSSObject ForcedSourceOnDiaObject ShearObject IsolatedStarStellarMotions"
FULLY_REPLICATED_TABLES="SSObject SSSource Visit VisitDetector CoaddPatches mpc_orbits current_identifications numbered_identifications"
ALL_TABLES="${PARTITIONED_TABLES} ${FULLY_REPLICATED_TABLES}"

# NOTE: Kubernetes-based deployments only!
# Prepare the confguration file qserv.json. The file will contain the authorization
# context for the subsequent operations performed by the ingest tools.
source make_config.source

APP=create-table-index
for TABLE in ${ALL_TABLES}; do
  for idx in $(ls ${INDEX_CONFIG} | grep "_${TABLE}_" | grep json); do
    LOG=${LOG_DIR}/${APP}-${idx::-5}.log;
    echo $(TIMESTAMP)"Create table index ${idx::-5} -> ${LOG}";
    ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} ${INDEX_CONFIG}/${idx} >& ${LOG};
    if [ $? -ne 0 ] ; then
      echo $(TIMESTAMP)FAILED;
      exit 1;
    fi;
  done;
done

echo $(TIMESTAMP)DONE

