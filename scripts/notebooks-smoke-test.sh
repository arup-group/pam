#!/usr/bin/env bash

set -e

pushd "${0%/*}"/..

python scripts/notebook_smoke_tests.py -d examples \
-k pam \
-k python37364bit373pyenve4f55e1c90f74740a9da8a10ea80341d \
-k python3

popd
