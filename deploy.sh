#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Google Cloud Project ID
PROJECT_ID="your-gcp-project-id"
# Google Cloud Function Name
FUNCTION_NAME="yahoo-finance-proxy"
# Google Cloud Region
REGION="us-central1"
# The entry point of your function
ENTRY_POINT="handler"

# --- Deployment ---
echo "Deploying function '$FUNCTION_NAME' to project '$PROJECT_ID' in region '$REGION'..."

gcloud functions deploy $FUNCTION_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --runtime=python312 \
  --trigger-http \
  --entry-point=$ENTRY_POINT \
  --allow-unauthenticated \
  --source=.

echo "Deployment successful."
echo "URL: $(gcloud functions describe $FUNCTION_NAME --project=$PROJECT_ID --region=$REGION --format='value(https.trigger.url)')"
