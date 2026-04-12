#!/usr/bin/env bash
set -euo pipefail

PORT=2024
GRAPH_ID="agent"
HOST="http://127.0.0.1:${PORT}"
CTX_JSON='{"user_id":"did:privy:cmmsl6t2402020cl2rperc5m1","is_expired":false,"evm_address":"0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E","sol_address":"GdV8W4x3WRsRM4Sdouh52Lxktfn1XyuaS6ETSvi8xssq"}'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
AID_FILE="${SCRIPT_DIR}/.lgdev_assistant_id"

kill_port() {
  local p="$1"
  local pids=""

  show_port_listeners "${p}" || true

  pids="$(lsof -tiTCP:${p} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "[lgdev] sending TERM to: ${pids}"
    kill -TERM ${pids} 2>/tmp/lgdev-kill.err || true
    sleep 1
  fi

  pids="$(lsof -tiTCP:${p} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "[lgdev] sending KILL to: ${pids}"
    kill -KILL ${pids} 2>/tmp/lgdev-kill.err || true
    sleep 1
  fi

  # fuser 双重确认
  if fuser "${p}/tcp" >/dev/null 2>&1; then
    fuser -k "${p}/tcp" 2>/tmp/lgdev-kill.err || true
    sleep 1
  fi

  pids="$(lsof -tiTCP:${p} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "[lgdev] failed to free port ${p}; still occupied by: ${pids}"
    if [[ -s /tmp/lgdev-kill.err ]]; then
      echo "[lgdev] kill error:"
      cat /tmp/lgdev-kill.err
    fi
    show_port_listeners "${p}" || true
    return 1
  fi
}

show_port_listeners() {
  local p="$1"
  local out
  out="$(lsof -nP -iTCP:${p} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "${out}" ]]; then
    echo "[lgdev] current listeners on :${p}"
    echo "${out}"
  fi
}

start_server() {
  uv run --with "langgraph-cli[inmem]" langgraph dev --config langgraph.json --no-reload --port "${PORT}" &
  LG_PID=$!
}

LG_PID=""
for attempt in 1 2; do
  if ! kill_port "${PORT}"; then
    echo "[lgdev] please clear manually and retry:"
    echo "  lsof -nP -iTCP:${PORT} -sTCP:LISTEN"
    echo "  kill -9 <PID>"
    exit 1
  fi

  if lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[lgdev] port ${PORT} is still occupied before start:"
    lsof -nP -iTCP:${PORT} -sTCP:LISTEN
    exit 1
  fi

  start_server

  i=0
  until curl -sf "${HOST}/ok" >/dev/null 2>&1; do
    if ! kill -0 "${LG_PID}" >/dev/null 2>&1; then
      wait "${LG_PID}" || true
      if [[ "${attempt}" == "1" ]]; then
        echo "[lgdev] first start failed; re-clean port ${PORT} and retry"
        break
      fi
      echo "[lgdev] langgraph dev exited before becoming ready"
      lsof -nP -iTCP:${PORT} -sTCP:LISTEN || true
      exit 1
    fi
    i=$((i + 1))
    if [[ "${i}" -gt 150 ]]; then
      echo "[lgdev] startup timeout"
      kill -TERM "${LG_PID}" 2>/dev/null || true
      exit 1
    fi
    sleep 0.2
  done

  if curl -sf "${HOST}/ok" >/dev/null 2>&1; then
    break
  fi
done

# 尝试从文件读取已保存的 assistant_id
saved_aid=""
if [[ -f "${AID_FILE}" ]]; then
  saved_aid="$(cat "${AID_FILE}" 2>/dev/null || true)"
fi

assign_or_create_assistant() {
  local patch_resp
  patch_payload="$(printf '{"context":%s}' "${CTX_JSON}")"

  if [[ -n "${saved_aid}" ]]; then
    # 尝试直接 patch 已保存的 id
    patch_resp="$(curl -s -w "%{http_code}" -X PATCH "${HOST}/assistants/${saved_aid}" \
      -H "Content-Type: application/json" \
      -d "${patch_payload}" 2>/dev/null)"
    if [[ "${patch_resp}" != "404"* ]]; then
      echo "[lgdev] assistant context updated (saved id): ${saved_aid}"
      echo "${saved_aid}" > "${AID_FILE}"
      return
    fi
    # id 不存在或 404，重新 search/create
    echo "[lgdev] saved assistant id ${saved_aid} not found, searching..."
  fi

  # search
  local search_payload="{\"graph_id\":\"${GRAPH_ID}\",\"limit\":20}"
  local aid="$(
    curl -s "${HOST}/assistants/search" \
      -H "Content-Type: application/json" \
      -d "${search_payload}" \
      | python3 -c 'import sys,json; d=json.load(sys.stdin); arr=d if isinstance(d,list) else (d.get("items") or d.get("assistants") or d.get("data") or []); print((arr[0] or {}).get("assistant_id","") if arr else "")' 2>/dev/null
  )"

  if [[ -n "${aid}" ]]; then
    curl -s -X PATCH "${HOST}/assistants/${aid}" \
      -H "Content-Type: application/json" \
      -d "${patch_payload}" >/dev/null
    echo "[lgdev] assistant context updated: ${aid}"
    echo "${aid}" > "${AID_FILE}"
  else
    local create_payload="{\"graph_id\":\"${GRAPH_ID}\",\"name\":\"Local Fixed Context\",\"context\":${CTX_JSON}}"
    local new_aid="$(
      curl -s -X POST "${HOST}/assistants" \
        -H "Content-Type: application/json" \
        -d "${create_payload}" \
        | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("assistant_id",""))' 2>/dev/null
    )"
    echo "[lgdev] assistant created with fixed context: ${new_aid}"
    echo "${new_aid}" > "${AID_FILE}"
  fi
}

assign_or_create_assistant

wait "${LG_PID}"
