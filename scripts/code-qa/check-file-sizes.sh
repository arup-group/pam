#!/bin/sh
#
# show large file sizes
# fail for size that is too large
# note that du is returning an indication of how much space the file uses not actual size

WARNING_SIZE=1000 #KB
TOO_LARGE=10000 #KB

echo "Starting check of new file sizes."
echo "File size warning threshold is set to $WARNING_SIZE KB"
echo "File size fail threshold is set to $TOO_LARGE KB"

# Redirect output to stderr.
exec 1>&2

CURRENT_DIR="$(pwd)"
HAS_WARNING=0
HAS_ERROR=0

for file in $(git diff --cached --name-only | sort | uniq); do
	file_size=$(du -k $CURRENT_DIR/$file | cut -f1)
	if [ "$file_size" -ge "$TOO_LARGE" ]; then
		echo "FAILURE $file is over $TOO_LARGE KB size ($file_size KB)."
		((HAS_ERROR++))
	elif [ "$file_size" -ge "$WARNING_SIZE" ]; then
		echo "WARNING $file is over $WARNING_SIZE KB size ($file_size KB)."
		((HAS_WARNING++))
	fi
done

if [ "$HAS_ERROR" != 0 ]; then
	echo "FAILURE: $HAS_ERROR files are over $TOO_LARGE KB."
    exit 1
fi
if [ "$HAS_ERROR" != 0 ]; then
	echo "WARNING: $HAS_WARNING files are over $WARNING_SIZE KB, are you sure these can't be made smaller?"
else
	echo "All good to proceed with these file sizes."
fi

