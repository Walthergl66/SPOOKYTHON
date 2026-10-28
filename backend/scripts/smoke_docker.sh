#!/usr/bin/env bash
set -euo pipefail

engine=${CONTAINER_ENGINE:-docker}
image=${NAVIRA_IMAGE:-navira-backend:local}
container="navira-smoke-$$"

if [[ "$engine" == podman ]]; then
  "$engine" build --format docker --file backend/Dockerfile --tag "$image" backend
else
  "$engine" build --file backend/Dockerfile --tag "$image" backend
fi
"$engine" run --detach --name "$container" --publish 127.0.0.1::8000 "$image" >/dev/null
trap '"$engine" rm --force "$container" >/dev/null 2>&1 || true' EXIT

port=$($engine port "$container" 8000/tcp | sed 's/.*://')
python3 - "$port" <<'PY'
import json
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

url = f"http://127.0.0.1:{sys.argv[1]}/salud"
deadline = time.monotonic() + 60
while True:
    try:
        with urlopen(url, timeout=2) as response:
            payload = json.load(response)
            if response.status != 200 or payload.get("estado") != "activo":
                raise SystemExit(f"Salud inesperada: HTTP {response.status}, {payload!r}")
            break
    except (OSError, URLError):
        if time.monotonic() >= deadline:
            raise SystemExit("El contenedor no respondió a /salud en 60 segundos")
        time.sleep(0.5)
print("GET /salud: HTTP 200; servicio activo")
PY

"$engine" exec "$container" test -s /opt/navira/backend/data/maps/manta-hackathon-v1.json
printf 'Fixture Manta: incluido\n'

runtime_user=$($engine inspect --format '{{.Config.User}}' "$container")
if [[ "$runtime_user" != navira ]]; then
  printf 'Usuario de ejecución inesperado: %s\n' "$runtime_user" >&2
  exit 1
fi
printf 'Usuario de ejecución: %s\n' "$runtime_user"

"$engine" stop --time 10 "$container" >/dev/null
exit_code=$($engine wait "$container")
if [[ "$exit_code" != 0 ]]; then
  printf 'El proceso no terminó limpiamente; código %s\n' "$exit_code" >&2
  exit 1
fi
printf 'Apagado SIGTERM: correcto\n'
