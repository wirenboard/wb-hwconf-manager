WBIO_NAME=()
WBIO_DIR=()
WBIO_COUNT=8
for ((i = 1; i <= WBIO_COUNT; i++)); do
	WBIO_NAME+=("DI$i")
	WBIO_DIR+=("input")
done

source "$DATADIR/modules/wbio.sh"
