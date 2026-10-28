#!/usr/bin/env bash
set -Eeuo pipefail

# Replace the single-process public demo containers on Lightsail, retaining
# their server-side configuration and rolling back to their prior image tags
# when the local health checks fail.

release_tag="${1:-}"
archive="${2:-}"
env_file="/etc/navira/public.env"
backend_name="navira-backend"
frontend_name="navira-frontend"

if [[ ! "$release_tag" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Expected a full 40-character Git commit SHA as release tag." >&2
  exit 2
fi
if [[ ! -f "$archive" ]]; then
  echo "Release archive not found: $archive" >&2
  exit 2
fi
if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this deployment script as root (for example, with sudo)." >&2
  exit 2
fi

cleanup() {
  rm -f -- "$archive"
}
trap cleanup EXIT

docker info >/dev/null

# Keep the existing runtime configuration on the instance. For the first
# automated update, migrate it from the running container without printing it.
if [[ ! -f "$env_file" ]]; then
  if ! docker inspect "$backend_name" >/dev/null 2>&1; then
    echo "Missing $env_file and no existing $backend_name container to migrate configuration from." >&2
    exit 3
  fi
  install -d -m 700 /etc/navira
  temp_env="$(mktemp /etc/navira/public.env.XXXXXX)"
  docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$backend_name" > "$temp_env"
  chmod 600 "$temp_env"
  mv "$temp_env" "$env_file"
fi
chmod 600 "$env_file"

if ! grep -Eq '^NAVIRA_PUBLIC_DEMO_CONTROL=1$' "$env_file"; then
  echo "Public demo is not enabled in $env_file; refusing deployment." >&2
  exit 3
fi
if ! grep -Eq '^NAVIRA_COOKIE_SECURE=1$' "$env_file"; then
  echo "Secure cookies must remain enabled in $env_file; refusing deployment." >&2
  exit 3
fi
if ! grep -Eq '^NAVIRA_API_KEY=.+$' "$env_file"; then
  echo "NAVIRA_API_KEY must be configured on the instance; refusing deployment." >&2
  exit 3
fi
if grep -Eq '^NAVIRA_LOCAL_DEMO_CONTROL=1$' "$env_file"; then
  echo "Local-only demo controls must remain disabled on the public instance." >&2
  exit 3
fi

old_backend_image=""
old_frontend_image=""
if docker inspect "$backend_name" >/dev/null 2>&1; then
  old_backend_image="$(docker inspect --format '{{.Config.Image}}' "$backend_name")"
fi
if docker inspect "$frontend_name" >/dev/null 2>&1; then
  old_frontend_image="$(docker inspect --format '{{.Config.Image}}' "$frontend_name")"
fi

rollback() {
  local rollback_ok=1
  echo "Deployment failed; restoring previous container images." >&2
  docker rm -f "$frontend_name" "$backend_name" >/dev/null 2>&1 || true
  if [[ -n "$old_backend_image" ]] && docker image inspect "$old_backend_image" >/dev/null 2>&1; then
    docker run -d --name "$backend_name" --network host --restart unless-stopped \
      --memory 3g --env-file "$env_file" "$old_backend_image" >/dev/null || rollback_ok=0
  else
    rollback_ok=0
  fi
  if [[ -n "$old_frontend_image" ]] && docker image inspect "$old_frontend_image" >/dev/null 2>&1; then
    docker run -d --name "$frontend_name" --network host --restart unless-stopped \
      "$old_frontend_image" >/dev/null || rollback_ok=0
  else
    rollback_ok=0
  fi
  if [[ "$rollback_ok" -eq 1 ]]; then
    wait_for_health || rollback_ok=0
  fi
  if [[ "$rollback_ok" -eq 1 ]]; then
    echo "Previous release restored." >&2
  else
    echo "Automatic rollback could not be fully verified; inspect Docker containers on the instance." >&2
  fi
}

wait_for_health() {
  local attempt
  for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8000/salud >/dev/null \
      && curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8080/ >/dev/null; then
      return 0
    fi
    sleep 2
  done
  return 1
}

wait_for_backend_health() {
  local attempt
  for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8000/salud >/dev/null; then
      return 0
    fi
    sleep 2
  done
  return 1
}

if ! gzip -t "$archive"; then
  echo "Release archive failed gzip integrity validation." >&2
  exit 4
fi
gzip -dc "$archive" | docker load
new_backend_image="navira-backend:${release_tag}"
new_frontend_image="navira-frontend:${release_tag}"
docker image inspect "$new_backend_image" "$new_frontend_image" >/dev/null

docker rm -f "$frontend_name" "$backend_name" >/dev/null 2>&1 || true
if ! docker run -d --name "$backend_name" --network host --restart unless-stopped \
  --memory 3g --env-file "$env_file" \
  --label "org.opencontainers.image.revision=${release_tag}" \
  "$new_backend_image" >/dev/null; then
  rollback
  exit 5
fi
if ! wait_for_backend_health; then
  rollback
  exit 6
fi

if ! docker run -d --name "$frontend_name" --network host --restart unless-stopped \
  --label "org.opencontainers.image.revision=${release_tag}" \
  "$new_frontend_image" >/dev/null; then
  rollback
  exit 7
fi
if ! wait_for_health; then
  rollback
  exit 8
fi

echo "Navira release ${release_tag} is healthy."
