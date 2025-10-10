#!/usr/bin/env bash
set -e

ENVIRONMENT=$1
if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: ./undeploy.sh [environment]"
  echo "Example: ./undeploy.sh prod"
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
REQUIRED=("SERVER" "PROJECT_NAME" "PROJECT_DIR" "API_PORT" "API_ROOT_PATH")
for VAR in "${REQUIRED[@]}"; do
  if [[ -z "${!VAR}" ]]; then
    echo "– missing required variable: $VAR"
    exit 1
  fi
done

echo "□ undeploying $PROJECT_NAME from $SERVER using $ENV_FILE"

ssh $SERVER bash << EOF
set -e

# docker
if [ -d "$PROJECT_DIR" ]; then
  echo "- stopping docker containers: $PROJECT_DIR"
  cd $PROJECT_DIR
  export PROJECT_NAME="$PROJECT_NAME"
  export API_PORT="$API_PORT"
  export API_ROOT_PATH=$API_ROOT_PATH
  docker compose down || true

  echo "- removing project directory: $PROJECT_DIR"
  sudo rm -rf $PROJECT_DIR
fi

# nginx
echo "- unconfiguring nginx: $PROJECT_NAME"
sudo rm -f /etc/nginx/sites-enabled/$PROJECT_NAME.conf
sudo rm -f /etc/nginx/sites-available/$PROJECT_NAME.conf
sudo nginx -t
sudo systemctl reload nginx

EOF

echo "■ undeploying $PROJECT_NAME from $SERVER using $ENV_FILE"
