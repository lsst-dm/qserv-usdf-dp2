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

#
# -- IMPORTANT --
#
# Tables have to be dropped in the reversed depedency order.
#
DELETE_TABLES="ForcedSource Object ShearObject ForcedSourceOnDiaObject DiaSourceOnDiaObject DiaSourceOnSSObject DiaSource DiaObject SSObject SSSource"
DIRECTOR_TABLES="Object DiaObject ShearObject DiaSourceOnSSObject"
PARTITIONED_TABLES="Object ForcedSource DiaObject DiaSource DiaSourceOnDiaObject DiaSourceOnSSObject ForcedSourceOnDiaObject ShearObject"
FULLY_REPLICATED_TABLES="SSObject SSSource"
ALL_TABLES="${PARTITIONED_TABLES} ${FULLY_REPLICATED_TABLES}"

# CSV dialect definitions for the tables
Object_CSV_DIALECT=
ForcedSource_CSV_DIALECT=
DiaObject_CSV_DIALECT=
DiaSource_CSV_DIALECT=
DiaSourceOnDiaObject_CSV_DIALECT=
DiaSourceOnSSObject_CSV_DIALECT=
ForcedSourceOnDiaObject_CSV_DIALECT=
ShearObject_CSV_DIALECT=
SSObject_CSV_DIALECT='--fields-enclosed-by="'
SSSource_CSV_DIALECT='--fields-enclosed-by="'

APP=delete-table
for TABLE in ${DELETE_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  echo $(TIMESTAMP)"Delete table ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

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
  echo $(TIMESTAMP)"Register table ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} ${TABLE_CONFIG}/${TABLE}.json >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

APP=async-contrib-chunks
for TABLE in ${PARTITIONED_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  CSV_DIALECT="${TABLE}_CSV_DIALECT";
  echo $(TIMESTAMP)"Ingest chunk contributions into ${TABLE} -> ${LOG}";
  #
  # -- IMPORTANT --
  #
  # Ingesting into all replicas in case if ingesting into previously published
  # database with th ereplication factor higher than 1.
  #  
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} --all-replicas  ${!CSV_DIALECT} ${VERBOSE_OPT} ${DEBUG_OPT} ${DATA_DIR}/${TABLE}.urls >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

APP=async-contrib-table-many
for TABLE in ${FULLY_REPLICATED_TABLES}; do
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

APP=create-director-index
for TABLE in ${DIRECTOR_TABLES}; do
  LOG=${LOG_DIR}/${APP}-${TABLE}.log;
  echo $(TIMESTAMP)"Create director index on ${TABLE} -> ${LOG}";
  ${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG};
  if [ $? -ne 0 ] ; then
    echo $(TIMESTAMP)FAILED;
    exit 1;
  fi;
done

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

echo $(TIMESTAMP)DONE

