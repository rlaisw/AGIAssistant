#!/bin/bash
# difyctl-export-reimport-publish.sh
# Complete workflow: Export → Re-import (Overwrite) → Publish Dify app
# Adopted (spec 024) from the operator's ~/Desktop original with three
# defects fixed: our app/workspace defaults, reachable error reporting,
# and JSON shape-checks that name the failed step.
# Usage: ./difyctl-export-reimport-publish.sh [APP_ID] [WORKSPACE_ID]

set -euo pipefail

# Defaults: AGI Assistant app + administrator's Workspace (DB-verified 2026-10-26)
APP_ID="${1:-194e1edf-2eba-442c-b10b-231bebb79c37}"
WORKSPACE_ID="${2:-af91d497-36b4-4940-9045-3d7415546381}"
EXPECTED_NAME="AGI Assistant"
EXPORT_DIR="${EXPORT_DIR:-$HOME/Downloads}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)_$$"
EXPORT_FILE="${EXPORT_DIR}/agi_assistant_export_${TIMESTAMP}.yml"

# Named-step JSON extraction: aborts naming the step on any parse/shape error.
# Error messages go to stderr so a set -e exit never swallows them.
json_get() {
    local expr="$1" step="$2" input="$3"
    local out
    if ! out=$(printf '%s' "${input}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d${expr})" 2>/dev/null); then
        echo "❌ ${step}: JSON parse failed or key ${expr} missing" >&2
        exit 1
    fi
    if [[ -z "${out}" || "${out}" == "None" ]]; then
        echo "❌ ${step}: key ${expr} is empty" >&2
        exit 1
    fi
    printf '%s' "${out}"
}

echo "=== Dify Export → Re-import (Overwrite) → Publish Workflow ==="
echo "App ID:       ${APP_ID}"
echo "Workspace ID: ${WORKSPACE_ID}"
echo "Export File:  ${EXPORT_FILE}"
echo ""

if [[ -z "${APP_ID}" || -z "${WORKSPACE_ID}" ]]; then
    echo "❌ config: APP_ID or WORKSPACE_ID is empty — aborting before any export"
    exit 1
fi

# Step 1: Export the app DSL
echo "📤 Step 1: Exporting app DSL..."
if ! EXPORT_OUTPUT=$(difyctl export console_app dsl --app-id "${APP_ID}" --json 2>&1); then
    echo "❌ Export failed: ${EXPORT_OUTPUT}"; exit 1
fi
YAML_CONTENT=$(json_get "['data']" "export" "${EXPORT_OUTPUT}")
DRAFT_HASH=$(json_get "['draft_hash']" "export" "${EXPORT_OUTPUT}")
echo "${YAML_CONTENT}" > "${EXPORT_FILE}"
echo "✅ Exported to: ${EXPORT_FILE}"
echo "📝 Draft hash: ${DRAFT_HASH}"
echo ""

# Step 2: Re-import with OVERWRITE mode (draft-hash guard: a mismatch means
# a concurrent edit — abort rather than overwrite with stale content)
echo "🔄 Step 2: Re-importing with OVERWRITE mode..."
if ! IMPORT_OUTPUT=$(difyctl import console_app dsl \
    --app-id "${APP_ID}" \
    --workspace-id "${WORKSPACE_ID}" \
    --mode yaml-content \
    --yaml-content "${YAML_CONTENT}" \
    --draft-hash "${DRAFT_HASH}" \
    --json 2>&1); then
    echo "❌ Re-import failed (draft-hash conflict = concurrent edit; re-export and retry): ${IMPORT_OUTPUT}"; exit 1
fi
IMPORT_ID=$(json_get ".get('id', 'n/a')" "re-import" "${IMPORT_OUTPUT}")
IMPORT_STATUS=$(json_get ".get('status', 'n/a')" "re-import" "${IMPORT_OUTPUT}")
echo "✅ Re-import completed: Import ID: ${IMPORT_ID}, Status: ${IMPORT_STATUS}"
echo ""

# Step 3: Publish the app
echo "🚀 Step 3: Publishing app..."
if ! PUBLISH_OUTPUT=$(difyctl publish console_app --app-id "${APP_ID}" --json 2>&1); then
    echo "❌ Publish failed: ${PUBLISH_OUTPUT}"; exit 1
fi
VERSION_ID=$(json_get ".get('version_id', d.get('data', {}).get('version_id', 'n/a'))" "publish" "${PUBLISH_OUTPUT}")
echo "✅ Published: Version ID: ${VERSION_ID}"
echo ""

# Step 4: Verify integrity — app id AND name must be unchanged.
# (The webapp access code is verified by the operator/battery via the
# Dify DB right after this script — it is not part of describe output.)
echo "🔍 Step 4: Verifying re-publish..."
if ! VERIFY_OUTPUT=$(difyctl describe console_app --app-id "${APP_ID}" --json 2>&1); then
    echo "❌ Verification failed: ${VERIFY_OUTPUT}"; exit 1
fi
VERIFY_APP_ID=$(json_get "['info']['id']" "verify" "${VERIFY_OUTPUT}")
VERIFY_NAME=$(json_get "['info']['name']" "verify" "${VERIFY_OUTPUT}")
echo "✅ Verification: App ID: ${VERIFY_APP_ID}, Name: ${VERIFY_NAME}"
echo ""

if [[ "${VERIFY_APP_ID}" != "${APP_ID}" ]]; then
    echo "❌ FAILURE: App ID changed! Expected: ${APP_ID}, Got: ${VERIFY_APP_ID}"; exit 1
fi
if [[ "${VERIFY_NAME}" != "${EXPECTED_NAME}" ]]; then
    echo "❌ FAILURE: App name changed! Expected: ${EXPECTED_NAME}, Got: ${VERIFY_NAME}"; exit 1
fi

echo ""
echo "🎉 SUCCESS: Complete workflow finished!"
echo "   - Exported to:   ${EXPORT_FILE}"
echo "   - Re-imported:   Import ID ${IMPORT_ID}"
echo "   - Published:     Version ID ${VERSION_ID}"
echo "   - Integrity:     App ID + name verified unchanged ✓"
