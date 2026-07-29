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

APP=alter-table-charset
TABLE=SSObject
CHARSET="utf8mb4"
COLLATION="utf8mb4_uca1400_ai_ci"
LOG=${LOG_DIR}/${APP}-${TABLE}.log
echo $(TIMESTAMP)"Changing table charset-collation ${TABLE} -> ${LOG}"
${TOOLS}/${APP}.py ${DATABASE_OPT} --table=${TABLE} "${CHARSET}" "${COLLATION}" ${VERBOSE_OPT} ${DEBUG_OPT} >& ${LOG}
if [ $? -ne 0 ] ; then
  echo $(TIMESTAMP)FAILED;
  exit 1;
fi


echo $(TIMESTAMP)DONE

