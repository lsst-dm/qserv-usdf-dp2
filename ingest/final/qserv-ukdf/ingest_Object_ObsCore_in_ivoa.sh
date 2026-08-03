#!/bin/bash

function TIMESTAMP {
  echo "[$(date +'%F %H:%M:%S')] "
}

BASE_DIR=$(dirname "$0")
if [ -z "$BASE_DIR" ] || [ "$0" = "bash" ]; then
    >&2 echo "error: variable 'BASE_DIR' is not defined"
    return 1
fi
BASE_DIR=$(readlink -e "$BASE_DIR")
if [ ! -d "$BASE_DIR" ]; then
    >&2 echo "error: path 'BASE_DIR' is not a valid directory"
    return 1
fi
LOG_DIR=${BASE_DIR}/logs
cd ${BASE_DIR}

rm -rf ${LOG_DIR}
mkdir -p ${LOG_DIR}

TOOLS=${BASE_DIR}/../../../tools
TABLE_CONFIG=${BASE_DIR}/../tables
INDEX_CONFIG=${BASE_DIR}/../indexes
DATA_DIR=${BASE_DIR}/../data-k8s-nginx

DATABASE=ivoa
DATABASE_OPT="--database=${DATABASE}"
ALL_REPLICAS_OPT="--all-replicas"
VERBOSE_OPT="--verbose"
DEBUG_OPT=

Object_CSV_DIALECT=
ObsCore_CSV_DIALECT='--fields-enclosed-by=" --fields-terminated-by=,'

# NOTE: Kubernetes-based deployments only!
# Prepare the confguration file qserv.json. The file will contain the authorization
# context for the subsequent operations performed by the ingest tools.
source make_config.source

APP=register-database
LOG=${LOG_DIR}/${APP}.log
echo $(TIMESTAMP)"Register database ${DATABASE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} ${VERBOSE_OPT} ${DEBUG_OPT} ../${DATABASE}.json >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

APP=register-table
for TABLE in Object ObsCore; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  echo $(TIMESTAMP)"Register table ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} ${TABLE_CONFIG}/${TABLE}.json >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

APP=async-contrib-chunks
TABLE=Object
LOG=${LOG_DIR}/${APP}-${TABLE}.log;
CSV_DIALECT="${TABLE}_CSV_DIALECT";
echo $(TIMESTAMP)"Ingest chunk contributions into ${TABLE} -> ${LOG}";
${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${!CSV_DIALECT} ${ALL_REPLICAS_OPT} ${VERBOSE_OPT} ${DEBUG_OPT} ${DATA_DIR}/${TABLE}-chunk-81376.urls >& ${LOG};
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

APP=async-contrib-table-many
TABLE=ObsCore
LOG=${LOG_DIR}/${APP}-${TABLE}.log
CSV_DIALECT="${TABLE}_CSV_DIALECT"
echo $(TIMESTAMP)"Ingest table contributions into ${TABLE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${!CSV_DIALECT}  ${VERBOSE_OPT} ${DEBUG_OPT} ${DATA_DIR}/${TABLE}.urls >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

APP=publish-database
LOG=${LOG_DIR}/${APP}.log
echo $(TIMESTAMP)"Publish database ${DATABASE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

APP=create-table-index
for TABLE in Object ObsCore; do
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

APP=rebuild-row-counters
for TABLE in Object ObsCore; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  echo $(TIMESTAMP)"Build row counter stats on ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

echo $(TIMESTAMP)DONE

