# Pushing Docker Images to Google Cloud Artifact Registry

This guide covers the complete workflow for pushing custom Docker images to Google Cloud Artifact Registry, including one-time setup and repeatable deployment steps.

## Phase 1: One-Time Setup

These steps only need to be performed once to configure your local machine.

### Step 1: Install Google Cloud CLI

Install the Google Cloud command-line interface, which is required for authenticating and managing your Google Cloud resources:

```bash
sudo snap install google-cloud-cli --classic
```

> **Note:** The `--classic` flag is required because the CLI needs broad system access.

### Step 2: Initialize and Authenticate gcloud

Configure gcloud to work with your Google Cloud account and project:

```bash
gcloud init
```

During the interactive setup process:

1. Choose **"Re-initialize this configuration"**
2. Select your Google Account (`nikita.dash.sh1rokov@gmail.com`)
3. Choose your cloud project (`rock-wonder-466311-g6`)

### Step 3: Configure Docker Authentication

Configure Docker to use your gcloud credentials when accessing Google's Artifact Registry:

```bash
# Replace us-central1 with your repository's region if different
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## Phase 2: Building and Pushing Images

Repeat these steps whenever you want to push a new version of your Docker image.

### Step 4: Tag Your Image

Tag your local Docker image with the full Artifact Registry path:

```bash
docker tag [LOCAL_IMAGE_NAME]:[TAG] [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:[TAG]
```

**Tag Format Breakdown:**
- `[REGION]-docker.pkg.dev` - Artifact Registry hostname (e.g., `us-central1-docker.pkg.dev`)
- `[PROJECT_ID]` - Your Google Cloud project ID
- `[REPOSITORY_NAME]` - Your repository name
- `[IMAGE_NAME]:[TAG]` - Image name and version tag

**Example:**
```bash
docker tag grchombo-dev:latest us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev:latest
```

### Step 5: Push to Artifact Registry

Upload your tagged image to Google Cloud:

```bash
docker push [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:[TAG]
```

**Example:**
```bash
docker push us-central1-docker.pkg.dev/rock-wonder-466311-g6/grchombo-repo/grchombo-dev:latest
```

## Summary

After completing these steps, your Docker image will be securely stored in your private Google Artifact Registry and available for deployment on any Google Cloud VM or service.

### Quick Reference for Future Pushes

For subsequent image versions, you only need to repeat Phase 2:

```bash
# Tag the new version
docker tag [LOCAL_IMAGE_NAME]:[NEW_TAG] [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:[NEW_TAG]

# Push to registry
docker push [REGION]-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/[IMAGE_NAME]:[NEW_TAG]
```