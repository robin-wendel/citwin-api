#!/usr/bin/env bash
set -e

ENVIRONMENT=$1
if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: ./deploy.sh [environment]"
  echo "Example: ./deploy.sh prod"
  exit 1
fi

# loading environment file
ENV_FILE=".env.deploy.$ENVIRONMENT"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "– environment file $ENV_FILE not found"
  exit 1
fi

# loading environment configuration
set -a
source "$ENV_FILE"
set +a


# ensuring required variables exist
REQUIRED=("SERVER" "PROJECT_NAME" "PROJECT_DIR" "GIT_REPO_URL" "GIT_BRANCH"  "API_PORT" "NGINX_CONF" "NGINX_DOMAIN")
for VAR in "${REQUIRED[@]}"; do
  if [[ -z "${!VAR}" ]]; then
    echo "– missing required variable: $VAR"
    exit 1
  fi
done

echo "□ deploying $PROJECT_NAME to $SERVER using $ENV_FILE"

ssh "$SERVER" bash << EOF
set -e

# git
if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "– cloning branch: $GIT_BRANCH"
  git clone -b "$GIT_BRANCH" "$GIT_REPO_URL" "$PROJECT_DIR"
else
  echo "– pulling branch: $GIT_BRANCH"
  cd "$PROJECT_DIR"
  git fetch origin
  git checkout "$GIT_BRANCH"
  git pull origin "$GIT_BRANCH"
fi
EOF

echo "– uploading env for docker"
scp .env.docker "$SERVER:$PROJECT_DIR/.env.docker"

ssh "$SERVER" bash << EOF
set -e
cd "$PROJECT_DIR"

# nginx
echo "– configuring nginx: $PROJECT_NAME"
sudo cp "$NGINX_CONF" /etc/nginx/sites-available/$PROJECT_NAME.conf
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME.conf /etc/nginx/sites-enabled/$PROJECT_NAME.conf
sudo nginx -t
sudo systemctl reload nginx

# docker
echo "– starting docker containers: $PROJECT_DIR"
export PROJECT_NAME="$PROJECT_NAME"
export API_PORT="$API_PORT"
export API_ROOT_PATH=$API_ROOT_PATH
docker compose down || true
docker compose up -d --build
EOF

echo "■ deploy: $PROJECT_NAME to $SERVER using $ENV_FILE"
