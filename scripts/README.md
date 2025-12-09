# TabWrap Scripts

Utility scripts for development, testing, and deployment of TabWrap.

## Deployment

### `deploy.sh` - Production Deployment Script

Automates deployment of TabWrap API updates to the production server (aegis VPS).

**Prerequisites:**
- Must be run on the production server (aegis VPS)
- Requires sudo access for systemd service management
- Poetry must be installed and in PATH

**Usage:**

```bash
# SSH to production server
ssh aegis

# Deploy latest from main branch
cd /opt/tabwrap-api
./scripts/deploy.sh

# Deploy specific version tag
./scripts/deploy.sh v1.3.0

# Explicitly deploy main branch (pulls latest)
./scripts/deploy.sh main
```

**What it does:**

1. Fetches latest code from GitHub
2. Checks out specified version/tag/branch
3. Installs Python dependencies with Poetry (production mode)
4. Restarts the systemd service (`tabwrap-api.service`)
5. Verifies the API is healthy and responding
6. Shows deployment summary and resource usage

**Example output:**

```
=========================================
TabWrap API Deployment
=========================================

[INFO] Changed to deployment directory: /opt/tabwrap-api

=========================================
Step 1/5: Fetching latest code from GitHub
=========================================

[INFO] Running: git fetch origin

=========================================
Step 2/5: Checking out version: v1.3.0
=========================================

[INFO] Checking out: v1.3.0
[SUCCESS] Now at: v1.3.0

...

[SUCCESS] Deployment completed successfully!
```

**Troubleshooting:**

If deployment fails, check:

```bash
# View service status
sudo systemctl status tabwrap-api

# View recent logs
sudo journalctl -fu tabwrap-api

# Check API health manually
curl http://127.0.0.1:8000/api/health
```

## Testing

### `smoke_test.py` - API Smoke Tests

Runs basic smoke tests against a TabWrap API instance to verify functionality.

**Usage:**

```bash
# Test local development server
poetry run python scripts/smoke_test.py

# Test production API
poetry run python scripts/smoke_test.py --url https://api.tabwrap.janfasnacht.com
```

## Workflow: Deploying a New Version

1. **Develop and test locally**
   ```bash
   # Make changes, test locally
   poetry run pytest
   poetry run python scripts/smoke_test.py
   ```

2. **Create release on GitHub**
   ```bash
   # Tag and push
   git tag v1.3.0
   git push origin v1.3.0
   ```

3. **Deploy to production**
   ```bash
   # SSH to server
   ssh aegis

   # Run deployment script
   cd /opt/tabwrap-api
   ./scripts/deploy.sh v1.3.0
   ```

4. **Verify deployment**
   ```bash
   # Check API is responding
   curl https://api.tabwrap.janfasnacht.com/api/health

   # Run smoke tests
   poetry run python scripts/smoke_test.py --url https://api.tabwrap.janfasnacht.com
   ```

## Notes

- The deployment script is designed to be idempotent - safe to run multiple times
- Always test locally before deploying to production
- The frontend (tabwrap-web) deploys automatically via Netlify on git push
- Backend deployments are manual and require SSH access to the VPS
