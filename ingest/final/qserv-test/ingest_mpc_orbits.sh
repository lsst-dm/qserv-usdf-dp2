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
TABLE_CONFIG=${BASE_DIR}/../tables
INDEX_CONFIG=${BASE_DIR}/../indexes
DATA_DIR=${BASE_DIR}/../data

# Variables that define a scope of the ingest
DATABASE=dp2
DATABASE_OPT="--database=${DATABASE}"
VERBOSE_OPT="--verbose"
DEBUG_OPT=
ALL_TABLES="mpc_orbits"

# Table parameters
mpc_orbits_TABLE_PARAMS="--charset=utf8mb4 --collation=utf8mb4_uca1400_ai_ci"

# CSV dialect definitions for the tables
mpc_orbits_CSV_DIALECT="--fields-enclosed-by=' --fields-terminated-by=,"

APP=unpublish-database
LOG=${LOG_DIR}/${APP}.log
echo $(TIMESTAMP)"Unpublish database ${DATABASE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

APP=register-table
for TABLE in ${ALL_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  TABLE_PARAMS="${TABLE}_TABLE_PARAMS";
  echo $(TIMESTAMP)"Register table ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${!TABLE_PARAMS} ${VERBOSE_OPT} ${DEBUG_OPT} ${TABLE_CONFIG}/${TABLE}.json >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

APP=async-contrib-table-many
for TABLE in ${ALL_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  CSV_DIALECT="${TABLE}_CSV_DIALECT";
  echo $(TIMESTAMP)"Ingest table contributions into ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${!CSV_DIALECT} ${VERBOSE_OPT} ${DEBUG_OPT} ${DATA_DIR}/${TABLE}.urls >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

APP=publish-database
LOG=${LOG_DIR}/${APP}.log
echo $(TIMESTAMP)"Publish database ${DATABASE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi

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

APP=rebuild-row-counters
for TABLE in ${ALL_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  echo $(TIMESTAMP)"Build row counter stats on ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done


# Fix the table schema

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

