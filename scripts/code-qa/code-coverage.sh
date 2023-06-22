#!/usr/bin/env bash

set -e

pushd "${0%/*}/../.."

pytest -vv \
--cov=. \
--cov-report=html:reports/coverage \
--cov-report=xml:reports/coverage/coverage.xml \
--cov-config=scripts/code-qa/.coveragerc \
tests/ mkdocs_plugins/
return_code=$?

popd

exit $return_code
