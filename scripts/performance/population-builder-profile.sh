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
    echo "usage: $script_name [-dabmrh]"
    echo "  -d    The full path to the travel diary CSV file to load (mandatory)"
    echo "  -a    The full path to the person attributes CSV file to load (mandatory)"
    echo "  -b    The mprof file to use as a benchmark; optional, no default"
    echo "  -m    The tolerance over the benchmark memory highpoint in MBs; defaults to 5"
    echo "  -r    The tolerance over the benchmark runtime in seconds; defaults to 5"
    echo "  -h    Display help"
    exit $1
}

function get_running_time() {
    profile_file=$1
    earliest_ts=`cat $profile_file | awk 'NR > 1 {print}' | head -n 1 | awk '{print $3}'`
    latest_ts=`cat $profile_file | tail -n 1 | awk '{print $3}'`
    running_time=`bc <<< "$latest_ts - $earliest_ts"`
    echo $running_time
}

function get_max_mem() {
    profile_file=$1
    max_mem=`cat $profile_file | awk '{print $2}' | sort -nr | head -n 1`
    echo $max_mem
}

while getopts ":d:a:b:m:r:h" opt; do
  case $opt in
    d) travel_diaries="$OPTARG"
    ;;
    a) person_attributes="$OPTARG"
    ;;
    b) benchmark_file="$OPTARG"
    ;;
    m) mem_tolerance="$OPTARG"
    ;;
    r) runtime_tolerance="$OPTARG"
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

if [[ -z "$mem_tolerance" ]]
then
    mem_tolerance='5'
fi

if [[ -z "$runtime_tolerance" ]]
then
    runtime_tolerance='5'
fi

if [[ -z "$benchmark_file" ]]
then
   printf "No benchmark file specified\n"
else
   printf "Using supplied profile file ${EM}${benchmark_file}${PLAIN} as a benchmark...\n"
   benchmark_running_time=`get_running_time $benchmark_file`
   printf "Benchmark run time was ${EM}${benchmark_running_time} seconds${PLAIN}\n"
   benchmark_max_mem=`get_max_mem $benchmark_file`
   printf "Benchmark max mem was ${EM}${benchmark_max_mem} MB${PLAIN}\n"
   printf "Benchmark mem tolerance is ${EM}${mem_tolerance} MB${PLAIN}\n"
   printf "Benchmark runtime tolerance is ${EM}${runtime_tolerance} seconds${PLAIN}\n"
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
mem_max=`get_max_mem $profile_file`
printf "Max memory from new profile file ${EM}${profile_file}${PLAIN} is ${EM}${mem_max} MB${PLAIN}\n"
running_time=`get_running_time $profile_file`
printf "Run time was ${EM}%s seconds${PLAIN}\n" "$running_time"

plot_file=`echo $profile_file | awk -F"." '{print $1}'`
printf "\nGenerating plot in ${EM}${plot_file}.png${PLAIN}...\n"
mprof plot $profile_file -o $plot_file -t "PAM Activity Loader Profile ($profile_file)"

if [[ -n "$benchmark_max_mem" ]]
then
    mem_usage_diff=`bc <<< "$mem_max - $benchmark_max_mem"`
    printf "Used ${EM}${mem_usage_diff}${PLAIN} MB more memory than the benchmark run\n"
    runtime_diff=`bc <<< "$running_time - $benchmark_running_time"`
    printf "Took ${EM}${runtime_diff}${PLAIN} seconds longer than the benchmark run\n"

    if (( $(echo "$mem_tolerance > $mem_usage_diff" | bc -l) ))
    then
      printf "\n${SUCCESS}${CHECKMARK_SYMBOL}  Memory usage is within ${mem_tolerance} MB tolerance of the benchmark \
${CHECKMARK_SYMBOL}${PLAIN}"
    else
      printf "\n${FAILURE}${CROSS_SYMBOL}  !!! Memory usage outside ${mem_tolerance} MB tolerance of the benchmark \
!!! ${CROSS_SYMBOL}${PLAIN}"
      return_value=1
    fi

    if (( $(echo "$runtime_tolerance > $runtime_diff" | bc -l) ))
    then
      printf "\n${SUCCESS}${CHECKMARK_SYMBOL}  Running time is within ${runtime_tolerance} seconds tolerance of the \
benchmark ${CHECKMARK_SYMBOL}${PLAIN}\n"
    else
      printf "\n${FAILURE}${CROSS_SYMBOL}  !!! Running time outside ${runtime_tolerance} seconds tolerance of the \
benchmark !!! ${CROSS_SYMBOL}${PLAIN}\n"
      return_value=1
    fi

    echo ""
fi

popd

exit $return_value
