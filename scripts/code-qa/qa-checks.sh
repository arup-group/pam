#!/usr/bin/env bash
#
# run tests and check coverage
# smoke test example notebooks
# show large file sizes
# fail for size that is too large


set -e

pushd "${0%/*}"

./code-coverage.sh
./notebooks-smoke-test.sh
./check-file-sizes.sh

popd
