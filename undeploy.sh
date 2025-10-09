#!/usr/bin/env bash
set -e

SERVER="adm_b1003527@zgis228.geo.sbg.ac.at"

ENVIRONMENT=$1

if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: ./undeploy.sh [staging|prod]"
  exit 1
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
  PROJECT_NAME="citwin-api-prod"
  PROJECT_DIR="/opt/citwin-api-prod"
elif [[ "$ENVIRONMENT" == "staging" ]]; then
  PROJECT_NAME="citwin-api-staging"
  PROJECT_DIR="/opt/citwin-api-staging"
else
  echo "Unknown environment: $ENVIRONMENT"
  exit 1
fi

echo "□ undeploy: $ENVIRONMENT"

ssh $SERVER bash << EOF
set -e

# docker
if [ -d "$PROJECT_DIR" ]; then
  echo "- stopping docker containers: $PROJECT_DIR"
  cd $PROJECT_DIR
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

echo "■ undeploy: $ENVIRONMENT"
