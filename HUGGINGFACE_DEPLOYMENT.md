# Vastu Shastra DSS - HuggingFace Spaces Deployment Guide

## Overview

This guide walks you through deploying the Vastu Shastra Decision Support System to HuggingFace Spaces for public access by 20 testers.

**Deployment Time:** 15-20 minutes  
**Public Access:** Yes (anyone with the link)  
**Testers:** Up to 20 concurrent users  

## Prerequisites

Before starting, ensure you have:
- GitHub account with access to `https://github.com/ajay2175/vastu-shastra-dss`
- HuggingFace account (free tier is sufficient)
- Anthropic API key (from https://console.anthropic.com)

## Step 1: Prepare Your Anthropic API Key

1. Visit https://console.anthropic.com/keys
2. Copy your API key
3. **IMPORTANT:** Do NOT share this key with anyone
4. Keep it ready for Step 4 below

## Step 2: Create HuggingFace Space

### Option A: Using HF Web UI (Easiest)

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"** button
3. Fill in the form:
   - **Space name:** `vastu-shastra-dss`
   - **Space type:** Docker
   - **License:** OpenRAIL (or your preferred open license)
   - **Visibility:** Public
4. Click **"Create Space"**

### Option B: Using HF CLI

```bash
huggingface-cli login
huggingface-cli repo create vastu-shastra-dss --type space --space-sdk docker --space-private false
```

## Step 3: Connect GitHub Repository

1. In your HuggingFace Space, go to **Settings** (top-right)
2. Under **Repository**, find **"Linked repositories"**
3. Click **"Link GitHub repo"**
4. Authenticate with GitHub
5. Select:
   - **Owner:** `ajay2175`
   - **Repository:** `vastu-shastra-dss`
   - **Branch:** `main`
6. Enable **"Auto-deploy"** (optional but recommended)
7. Click **"Link"**

**Result:** The Space will automatically pull from GitHub and deploy

## Step 4: Configure Environment Secrets

This is the MOST CRITICAL step. The API requires your Anthropic API key.

### Via HuggingFace UI:

1. Go to your Space settings
2. Click **"Repository secrets"** (or "Secret variables")
3. Add new secret:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** (paste your API key from Step 1)
   - **Click:** "Add secret"
4. The Space will automatically restart with the new secret

### IMPORTANT: Secret Format

- Copy the API key **exactly as is**
- Remove any leading/trailing whitespace
- If the key has newlines (multi-line format), convert to single line
- Example correct format: `sk-ant-v0-abc123def456...` (single line)

## Step 5: Initial Deployment Build

The Space will start building automatically. You'll see:

1. **Building status:** Watch the build progress in the Space logs
2. **Startup time:** Initial build takes 3-5 minutes
3. **Health check:** The app has 90 seconds to respond to health checks

### Monitor Build Progress:

1. Click on your Space name
2. View logs at the bottom of the page
3. Look for status messages like:
   - ✅ Dependencies installed
   - ✅ Code copied
   - ✅ Container starting
   - ✅ Health check passed

## Step 6: Verify Deployment

Once the Space shows "Running":

1. Click the **"App"** tab in your Space
2. You should see the FastAPI Swagger UI
3. Open **`/docs`** endpoint (appears in the UI)
4. Test a simple endpoint like `/health`

### First Test Request:

```bash
# In your terminal
curl https://YOUR_SPACE_URL/health
```

Expected response:
```json
{
  "status": "operational",
  "timestamp": "2024-10-08T...",
  "version": "4.0.0"
}
```

## Step 7: Share With Testers

Once verified, share the link with your 20 testers:

### Shareable Link Format:
```
https://huggingface.co/spaces/YOUR_USERNAME/vastu-shastra-dss
```

### What Testers See:
- Live web interface showing the API
- Swagger UI at `/docs` for interactive testing
- All endpoints documented with try-it-out buttons

## API Endpoints Available

Testers can use these endpoints directly:

### Space Analysis
```
POST /api/v1/analyze-space
```
Request:
```json
{
  "space_type": "living_room",
  "dimensions": {"length": 20, "width": 15, "height": 10},
  "direction": "north",
  "current_state": "cluttered"
}
```

### Direction Consultation
```
POST /api/v1/consult/direction
```
Request:
```json
{
  "direction": "northeast",
  "space_type": "bedroom",
  "query": "bedroom placement advice"
}
```

### Room Consultation
```
POST /api/v1/consult/room
```
Request:
```json
{
  "room_type": "kitchen",
  "query": "improve kitchen energy"
}
```

### System Health
```
GET /health
```

## Troubleshooting

### Issue: Space shows "Failed to build"

**Solution:**
1. Check the build logs (scroll in the Space logs area)
2. Common causes:
   - Missing dependency in requirements.txt
   - Syntax error in code
   - Insufficient disk space

**Fix:** Check GitHub repo for any uncommitted changes and redeploy:
```bash
cd /Users/ajaynawale/vastu_shastra_dss
git status
git push origin main
```

### Issue: API returns 500 error or no response

**Solution:**
1. Check if ANTHROPIC_API_KEY is set:
   - Go to Space settings → "Repository secrets"
   - Verify ANTHROPIC_API_KEY is listed
   - If missing, add it and wait 2 minutes for restart
2. Check logs in Space (scroll to see error messages)

### Issue: Slow response time

**Expected:** First request takes 5-10 seconds (model loading)  
**Subsequent:** 2-5 seconds per request

If consistently slow:
1. Check if 20 testers are all requesting simultaneously
2. HuggingFace may need to scale resources
3. Contact support if issues persist

### Issue: Testers report "Connection refused"

**Solution:**
1. Verify Space is in "Running" state (not "Building" or "Stopped")
2. Restart Space:
   - Settings → "Restart Space"
   - Wait 30-60 seconds
3. Share the correct URL (check in browser address bar)

## Monitoring Performance

### View Space Logs:

1. Click on your Space
2. Scroll to bottom → "Logs"
3. Look for:
   - `API: operational` - Server is running
   - `Request received` - Requests are being processed
   - Any error messages

### Get System Status:

```bash
# Test endpoint availability
curl https://YOUR_SPACE_URL/health

# Test diagnosis endpoint
curl -X POST https://YOUR_SPACE_URL/api/v1/consult/direction \
  -H "Content-Type: application/json" \
  -d '{"direction": "north", "space_type": "bedroom", "query": "test"}'
```

## Important Notes

### Data Privacy
- The Space runs on HuggingFace infrastructure
- Your Anthropic API key is stored as a secret variable
- API calls go through Anthropic (standard API calls)

### Rate Limiting
- HuggingFace allows reasonable usage
- Avoid stress testing with excessive concurrent requests
- If you need high volume testing, contact HF support

### Updating Code
- If you push changes to `main` branch on GitHub
- Space automatically redeploys (if auto-deploy enabled)
- Typical redeploy time: 60-90 seconds

### Stopping/Pausing Space
- To pause: Settings → "Pause Space" (saves credits)
- To resume: Click "Resume" in Space view
- Paused spaces don't consume credits but aren't accessible

## Success Checklist

- [ ] Created HuggingFace Space with name `vastu-shastra-dss`
- [ ] Connected GitHub repository (`ajay2175/vastu-shastra-dss`)
- [ ] Added ANTHROPIC_API_KEY secret
- [ ] Space shows "Running" status
- [ ] `/health` endpoint returns 200 OK
- [ ] Swagger UI loads at `/docs`
- [ ] At least one test request succeeds
- [ ] Shared public link with testers
- [ ] Received confirmation from 2+ testers that they can access

## Support

For issues:
1. Check Vastu Shastra DSS logs: https://huggingface.co/spaces/YOUR_USERNAME/vastu-shastra-dss
2. Check GitHub issues: https://github.com/ajay2175/vastu-shastra-dss/issues
3. For HuggingFace-specific issues: https://huggingface.co/support

## Next Steps After Deployment

1. Share link with testers
2. Collect feedback in first 24 hours
3. Monitor logs for any errors
4. Be ready to add additional environment variables if needed
5. After testing, update code based on feedback

---

**Version:** 1.0  
**Last Updated:** October 8, 2024  
**Deployment Status:** Ready to deploy
