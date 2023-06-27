#!/bin/bash

# exit script if any step returns a non-0 code
set -e

echo "Executing environment tests..."

pytest -vv tests/ mkdocs_plugins/
./scripts/code-qa/notebooks-smoke-test.sh

echo "Tests complete"
