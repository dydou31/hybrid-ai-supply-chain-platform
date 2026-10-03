#!/bin/bash

set -e

URL="http://hybrid-ai-alb-1065226339.eu-west-3.elb.amazonaws.com/suppliers"
DURATION=120
CONCURRENCY=50

echo "=================================================="
echo "       HYBRID AI PLATFORM - LOAD GENERATOR"
echo "=================================================="
echo
echo "Target      : $URL"
echo "Duration    : ${DURATION}s"
echo "Concurrency : $CONCURRENCY"
echo
echo "Generating load..."
echo "Ctrl+C to stop"
echo

END=$((SECONDS + DURATION))
WAVE=1

while [ $SECONDS -lt $END ]; do
  echo "Load wave $WAVE - $(date '+%H:%M:%S')"

  seq 1 500 | xargs -P "$CONCURRENCY" -I {} \
    curl -s --max-time 5 -o /dev/null "$URL"

  WAVE=$((WAVE + 1))
done

echo
echo "=================================================="
echo "          LOAD GENERATION COMPLETE"
echo "=================================================="
