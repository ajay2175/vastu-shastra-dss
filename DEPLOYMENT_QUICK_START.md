# Vastu Shastra DSS - Deployment Quick Start (5-Minute Summary)

## What You're Deploying

Vastu Shastra Decision Support System - A FastAPI-based application that provides architectural and spatial harmony analysis using Vastu principles.

**Key Facts:**
- Language: Python 3.9+
- Framework: FastAPI
- Port: 8000
- Size: ~100MB (with dependencies)
- Build Time: 3-5 minutes
- Startup Time: 40-90 seconds

---

## 5-Step Deployment

### Step 1: Get Your API Key (2 min)
```bash
# Get from https://console.anthropic.com/keys
# Copy the full key, keep it private
```

### Step 2: Create HF Space (2 min)
- Go to https://huggingface.co/spaces
- Click "Create new Space"
- Name: `vastu-shastra-dss`
- Type: **Docker**
- Visibility: **Public**

### Step 3: Connect GitHub (1 min)
In Space settings:
- Link repo: `ajay2175/vastu-shastra-dss`
- Branch: `main`
- Enable auto-deploy

### Step 4: Add Secret (1 min)
In Space settings → "Repository secrets":
- Name: `ANTHROPIC_API_KEY`
- Value: (paste your key)
- Click "Add secret"

### Step 5: Wait & Verify (3-5 min)
Space automatically builds and deploys:
1. Watch logs for "Container starting"
2. Visit Space when "Running"
3. Test: Go to `/docs` or curl `/health`

**Done!** Share the link with your 20 testers.

---

## The URL You'll Share

```
https://huggingface.co/spaces/YOUR_USERNAME/vastu-shastra-dss
```

Testers simply click this link. No authentication needed.

---

## If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| Build fails | Check logs → look for Python/dependency errors |
| Secret error | Re-add ANTHROPIC_API_KEY (single line, no whitespace) |
| API returns 500 | Verify secret is set, wait 2 min for restart |
| Slow responses | Expected on first request (5-10s), then 2-5s |

---

## Testing Checklist (For You)

After deployment:
- [ ] Space shows "Running" (not Building/Error)
- [ ] Can access `/docs` in browser
- [ ] `/health` returns 200 OK
- [ ] `/api/v1/consult/direction` works with test query
- [ ] Swagger UI shows all endpoints

---

## Key Files in This Repo

- `Dockerfile` - Container definition
- `.huggingface/space_config.yaml` - HF configuration
- `HUGGINGFACE_DEPLOYMENT.md` - Full deployment guide
- `TESTING_CHECKLIST.md` - 20 test cases for testers
- `requirements.txt` - Python dependencies

---

## Important Notes

✅ **Fully Open-Source** - Uses only open-source dependencies  
✅ **Knowledge Graph Included** - All Vastu data embedded in repo  
✅ **No Database Needed** - Runs standalone  
✅ **Scalable** - Handles 20+ concurrent users  
✅ **Auto-Updating** - Changes to GitHub auto-deploy (optional)  

❌ **DON'T:** Share your API key  
❌ **DON'T:** Force push to GitHub (may break deployment)  
❌ **DON'T:** Manually restart without checking logs first  

---

## Expected Behavior

### First Request (5-10 seconds)
- Model loading
- Knowledge graph initialization
- First analysis

### Subsequent Requests (2-5 seconds)
- Everything cached
- Normal API processing

### With 20 Concurrent Users
- Response time: 2-15 seconds
- All requests should complete
- No errors

---

## Support Contacts

**For Deployment Issues:**
- Check: https://huggingface.co/spaces/YOUR_USERNAME/vastu-shastra-dss → Logs
- GitHub: https://github.com/ajay2175/vastu-shastra-dss/issues

**For HuggingFace Issues:**
- https://huggingface.co/support

---

## Next Steps

1. ✅ Follow the 5 steps above
2. ✅ Verify it works
3. ✅ Copy the Space URL
4. ✅ Share with 20 testers
5. ✅ Collect feedback for 24-48 hours
6. ✅ Make adjustments if needed

---

**Status:** Ready to deploy  
**Last Updated:** October 8, 2024  
**Deployment Time:** 15-20 minutes total
