#!/usr/bin/env bash
set -e

SERVER="adm_b1003527@zgis228.geo.sbg.ac.at"
REPO_URL="https://github.com/robin-wendel/citwin-api.git"

ENVIRONMENT=$1

if [[ -z "$ENVIRONMENT" ]]; then
  echo "Usage: ./deploy.sh [staging|prod]"
  exit 1
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
  GIT_BRANCH="dev"
  PROJECT_NAME="citwin-api-prod"
  PROJECT_DIR="/opt/citwin-api-prod"
  API_PORT=8001
  API_ROOT_PATH="/api/citwin-prod"
  NGINX_CONF="nginx/prod.conf"
elif [[ "$ENVIRONMENT" == "staging" ]]; then
  GIT_BRANCH="dev"
  PROJECT_NAME="citwin-api-staging"
  PROJECT_DIR="/opt/citwin-api-staging"
  API_PORT=9001
  API_ROOT_PATH="/api/citwin-staging"
  NGINX_CONF="nginx/staging.conf"
else
  echo "Unknown environment: $ENVIRONMENT"
  exit 1
fi

echo "□ deploy: $ENVIRONMENT"

ssh $SERVER bash << EOF
set -e

if [ ! -d "$PROJECT_DIR/.git" ]; then
  echo "– cloning branch: $GIT_BRANCH"
  git clone -b $GIT_BRANCH $REPO_URL $PROJECT_DIR
else
  echo "– pulling branch: $GIT_BRANCH"
  cd $PROJECT_DIR
  git fetch origin
  git checkout $GIT_BRANCH
  git pull origin $GIT_BRANCH
fi

cd $PROJECT_DIR

# nginx
echo "– configuring nginx: $PROJECT_NAME"
sudo cp $NGINX_CONF /etc/nginx/sites-available/$PROJECT_NAME.conf
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME.conf /etc/nginx/sites-enabled/$PROJECT_NAME.conf
sudo nginx -t
sudo systemctl reload nginx

# docker
echo "– starting docker containers: $PROJECT_DIR"
export PROJECT_NAME=$PROJECT_NAME
export API_ROOT_PATH=$API_ROOT_PATH
export API_PORT=$API_PORT
docker compose up -d --build
EOF

echo "■ deploy: $ENVIRONMENT"
