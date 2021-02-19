#!/usr/bin/env bash

set -e

pushd "${0%/*}"
pushd ..

python3 -m pytest -vv \
--cov=. \
--cov-report=html:reports/coverage \
--cov-report=xml:reports/coverage/coverage.xml \
--cov-config=scripts/.coveragerc \
tests/
return_code=$?

popd
popd
exit $return_code
