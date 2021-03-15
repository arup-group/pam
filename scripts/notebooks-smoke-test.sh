#!/usr/bin/env bash

set -e

pushd "${0%/*}"/..

python notebooks/notebook_smoke_tests.py -d notebooks -k pam

popd
