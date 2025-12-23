#!/usr/bin/env bash
# Minimal wait-for-it script to wait for host:port availability
# Usage: ./scripts/wait-for-it.sh [-t seconds] host:port
TIMEOUT=60

usage() {
  echo "Usage: $0 [-t seconds] host:port"
  exit 1
}

while getopts ":t:" opt; do
  case ${opt} in
    t ) TIMEOUT=$OPTARG ;;
    * ) usage ;;
  esac
done
shift $((OPTIND -1))

if [ $# -ne 1 ]; then
  usage
fi

HOSTPORT=$1
HOST=${HOSTPORT%%:*}
PORT=${HOSTPORT##*:}

start_ts=$(date +%s)
while :; do
  if command -v nc >/dev/null 2>&1; then
    if nc -z "$HOST" "$PORT" >/dev/null 2>&1; then
      echo "OK: $HOST:$PORT is available"
      exit 0
    fi
  else
    # fallback to /dev/tcp (works in bash)
    if (echo > /dev/tcp/"$HOST"/"$PORT") >/dev/null 2>&1; then
      echo "OK: $HOST:$PORT is available"
      exit 0
    fi
  fi

  now=$(date +%s)
  elapsed=$((now - start_ts))
  if [ "$elapsed" -ge "$TIMEOUT" ]; then
    echo "Timeout after ${TIMEOUT}s waiting for $HOST:$PORT"
    exit 1
  fi
  sleep 1
done
