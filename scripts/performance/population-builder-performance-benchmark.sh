#!/usr/bin/env bash
###########################################################
# Build a population of 230000 people in 200000 households
# and compare running time and memory usage to a known
# benchmark.
###########################################################


pushd "${0%/*}"

./population-builder-profile.sh \
-d test-data/simple_travel_diaries.gz  \
-a test-data/simple_persons_data.gz \
-b `realpath pop-builder-perf-benchmark.dat` \
-m 20 \
-r 10

popd