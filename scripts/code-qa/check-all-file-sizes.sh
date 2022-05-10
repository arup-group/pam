#!/usr/bin/env bash
#
# show large file sizes
# fail for size that is too large
# note that du is returning an indication of how much space the file uses not actual size

shopt -s globstar

WARNING_SIZE_KB=1000 #KB
TOO_LARGE_KB=10000 #KB

echo "Starting check of all project file sizes."
echo "File size warning threshold is set to $WARNING_SIZE_KB KB"
echo "File size fail threshold is set to $TOO_LARGE_KB KB"
echo "-----------"

pushd "${0%/*}/../.." > /dev/null

HAS_WARNING=0
HAS_ERROR=0

for file in ./[^.]* ./**/[^.]* ; do
    if test -f "$file"; then
        file_size=$(du -k "$file" | cut -f1)
        if [ "$file_size" -ge "$TOO_LARGE_KB" ]; then
            echo "FAILURE $file is over $TOO_LARGE_KB KB size ($file_size KB)."
            ((HAS_ERROR++))
        elif [ "$file_size" -ge "$WARNING_SIZE_KB" ]; then
            echo "WARNING $file is over $WARNING_SIZE_KB KB size ($file_size KB)."
            ((HAS_WARNING++))
        fi
    fi
done

echo "-----------"

popd > /dev/null

if [ "$HAS_ERROR" != 0 ]; then
    echo "FAILURE: $HAS_ERROR files are over $TOO_LARGE_KB KB."
    exit $HAS_ERROR
fi
if [ "$HAS_ERROR" != 0 ]; then
    echo "WARNING: $HAS_WARNING files are over $WARNING_SIZE_KB KB, are you sure these can't be made smaller?"
else
    echo "All good to proceed with these file sizes."
fi

