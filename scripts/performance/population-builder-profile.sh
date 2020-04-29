#!/usr/bin/env bash
###########################################################
# Script to profile PAM's population building for both
# running time and memory footprint.
#
# Author: Michael Fitzmaurice, April 2020
###########################################################

# text colours
PLAIN='\033[0m'
EM='\033[0;93m'
QUOTE='\033[0;34m'
SUCCESS='\033[0;32m'
FAILURE='\033[0;31m'

CHECKMARK_SYMBOL='\xE2\x9C\x94'
CROSS_SYMBOL='\xE2\x9D\x8C'

script_name=$0
function usage() {
    echo ""
    echo "usage: $script_name [-tah]"
    echo "  -t    The full path to the travel diary CSV file to load (mandatory)"
    echo "  -a    The full path to the person attributes CSV file to load (mandatory)"
    echo "  -h    Display help"
    exit $1
}

while getopts ":t:a:h" opt; do
  case $opt in
    t) travel_diaries="$OPTARG"
    ;;
    a) person_attributes="$OPTARG"
    ;;
    h) usage 0
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [[ -z "$travel_diaries" ]] || [[ -z "$person_attributes" ]]
then
  printf "${FAILURE} !!! You did not supply all the necessary mandatory parameters - exiting !!!${PLAIN}"
  usage 1
fi

pushd "${0%/*}"
printf "\nProfiling PAM population building....\n"

printf "Running PAM activity loader...\n"
printf "\n${QUOTE}-----------------------------------------------\n"
export PYTHONPATH=../..
env | grep -i pythonpath
mprof run --python  --include-children --exit-code python activity_loader.py -t $travel_diaries -a $person_attributes
return_code=$?
echo "-----------------------------------------------"
printf "\n${PLAIN}"

if test $return_code -eq 0
then
  printf "PAM loader exited normally\n"
else
  printf "${FAILURE}${CROSS_SYMBOL}  !!! PAM loader exited with an error (exit code=${return_code})!!! \
${CROSS_SYMBOL}\n${PLAIN}"
  exit $return_code
fi

profile_file=`ls -talh mprofile_* | head -n 1 | awk '{print $NF}'`
mem_max=`cat $profile_file | awk '{print $2}' | sort -nr | head -n 1`
printf "Max memory from new profile file ${EM}%s${PLAIN} is ${EM}%s${PLAIN}\n" "$profile_file" "$mem_max"
earliest_ts=`cat $profile_file | awk 'NR > 1 {print}' | head -n 1 | awk '{print $3}'`
latest_ts=`cat $profile_file | tail -n 1 | awk '{print $3}'`
printf "Earliest timestamp from new profile file ${EM}%s${PLAIN} is ${EM}%s${PLAIN}\n" "$profile_file" "$earliest_ts"
printf "Latest timestamp from new profile file ${EM}%s${PLAIN} is ${EM}%s${PLAIN}\n" "$profile_file" "$latest_ts"
running_time=`bc <<< "$latest_ts - $earliest_ts"`
printf "Run time was ${EM}%s${PLAIN} seconds\n" "$running_time"
