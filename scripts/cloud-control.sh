#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$#" -ne 1 || ( "$1" != "on" && "$1" != "off" ) ]]; then
  echo "Usage: $0 {on|off}" >&2
  exit 2
fi

ACTION="$1"

# Utiliser explicitement le compte AWS du projet.
export AWS_PROFILE="hybrid-ai-terraform"
export AWS_DEFAULT_REGION="eu-west-3"
LOCK_FILE="${TMPDIR:-/tmp}/hybrid-ai-cloud.lock"

exec lockf -t 0 "$LOCK_FILE" \
  /usr/bin/env HYBRID_AI_CLOUD_SUPERVISED=1 \
  python3 "$SCRIPT_DIR/cloud-lock.py" run -- \
  /bin/bash "$SCRIPT_DIR/cloud-$ACTION.sh"
