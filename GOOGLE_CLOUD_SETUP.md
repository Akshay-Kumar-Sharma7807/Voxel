# Google Cloud Setup for Voxel Image Generation

This guide will help you set up Google Cloud Vertex AI for image generation using the Imagen model.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud Project** with Vertex AI API enabled
3. **Service Account** with appropriate permissions

## Step-by-Step Setup

### 1. Create Google Cloud Project

```bash
# Install Google Cloud CLI if not already installed
# Visit: https://cloud.google.com/sdk/docs/install

# Create a new project (or use existing)
gcloud projects create voxel-ambient-art --name="Voxel Ambient Art"

# Set the project as default
gcloud config set project voxel-ambient-art
```

### 2. Enable Required APIs

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Resource Manager API (if needed)
gcloud services enable cloudresourcemanager.googleapis.com
```

### 3. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create voxel-image-generator \
    --description="Service account for Voxel image generation" \
    --display-name="Voxel Image Generator"

# Grant necessary permissions
gcloud projects add-iam-policy-binding voxel-ambient-art \
    --member="serviceAccount:voxel-image-generator@voxel-ambient-art.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download service account key
gcloud iam service-accounts keys create voxel-credentials.json \
    --iam-account=voxel-image-generator@voxel-ambient-art.iam.gserviceaccount.com
```

### 4. Set Environment Variables

Create a `.env` file in your project root:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=voxel-ambient-art
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=./voxel-credentials.json

# Set image provider to Google Cloud
IMAGE_PROVIDER=google_cloud
```

Or set them in your system:

```bash
# Windows
set GCP_PROJECT_ID=voxel-ambient-art
set GCP_LOCATION=us-central1
set GOOGLE_APPLICATION_CREDENTIALS=./voxel-credentials.json
set IMAGE_PROVIDER=google_cloud

# Linux/Mac
export GCP_PROJECT_ID=voxel-ambient-art
export GCP_LOCATION=us-central1
export GOOGLE_APPLICATION_CREDENTIALS=./voxel-credentials.json
export IMAGE_PROVIDER=google_cloud
```

### 5. Install Dependencies

```bash
pip install google-cloud-aiplatform vertexai
```

### 6. Test the Setup

```bash
python examples/test_image_generator.py
```

## Available Regions

Vertex AI Imagen is available in these regions:
- `us-central1` (Iowa)
- `us-east4` (Northern Virginia)
- `us-west1` (Oregon)
- `europe-west4` (Netherlands)
- `asia-southeast1` (Singapore)

## Pricing

Google Cloud Vertex AI Imagen pricing (as of 2024):
- **Imagen 2**: ~$0.020 per image (1024x1024)
- **Imagen 3**: ~$0.040 per image (1024x1024)

Check current pricing: https://cloud.google.com/vertex-ai/generative-ai/pricing

## Troubleshooting

### Authentication Issues
```bash
# Verify authentication
gcloud auth application-default login

# Check service account permissions
gcloud projects get-iam-policy voxel-ambient-art
```

### API Not Enabled
```bash
# List enabled APIs
gcloud services list --enabled

# Enable Vertex AI if missing
gcloud services enable aiplatform.googleapis.com
```

### Quota Issues
- Check your project quotas in Google Cloud Console
- Request quota increases if needed
- Monitor usage in Cloud Monitoring

## Security Best Practices

1. **Limit Service Account Permissions**: Only grant `roles/aiplatform.user`
2. **Rotate Keys Regularly**: Create new service account keys periodically
3. **Use IAM Conditions**: Add time-based or IP-based restrictions
4. **Monitor Usage**: Set up billing alerts and usage monitoring

## Alternative: Using User Credentials

Instead of service account, you can use user credentials:

```bash
# Authenticate with your user account
gcloud auth application-default login

# Set project
gcloud config set project voxel-ambient-art
```

Then you don't need `GOOGLE_APPLICATION_CREDENTIALS`, just set:
```bash
GCP_PROJECT_ID=voxel-ambient-art
IMAGE_PROVIDER=google_cloud
```