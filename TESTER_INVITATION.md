# Vastu Shastra DSS - Tester Invitation

## You're Invited to Test the Vastu Shastra Decision Support System!

Hi! We're launching a new AI-powered decision support system for Vastu Shastra (the ancient Indian science of architecture and spatial harmony). **We need 20 testers like you to help validate the system before full release.**

---

## What You'll Be Testing

A web-based API that provides:
- ✅ Directional consultation (North, East, South, West, etc.)
- ✅ Room-by-room Vastu analysis (Bedroom, Kitchen, Office, etc.)
- ✅ Space defect diagnosis and remediation
- ✅ Personalized recommendations based on Vastu principles

---

## How to Access

**Public Link:** [DEPLOYMENT_URL]

**No sign-up required!** Just click the link and start testing.

### What You'll See:
1. **Swagger UI** - Interactive API documentation
2. **Live endpoint tester** - Try requests with one click
3. **Real responses** - From the Vastu Shastra DSS

---

## Your Testing Tasks

You'll run 20 tests covering:
- System health checks
- Direction-based consultations
- Room analysis
- Space defect diagnosis
- Performance under load

**Estimated Time:** 2-3 hours (can be done over 2-3 days)

See [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md) for detailed test cases.

---

## What We Need From You

For each test, provide:
1. ✅ **Did it work?** (Success / Partial / Failed)
2. ⏱️ **How fast?** (Response time in seconds)
3. 💬 **Feedback** (Was the answer helpful? Any errors?)
4. ⭐ **Overall rating** (1-5 stars)
5. 📝 **Issues found** (If any, with details)

---

## Sharing Your Feedback

### Option 1: GitHub Issues (Technical)
Report issues here: https://github.com/ajay2175/vastu-shastra-dss/issues

**Include:**
- Test number
- Exact error message
- Your response time
- Screenshot (if UI issue)

### Option 2: Email (General Feedback)
Send feedback to: [YOUR_EMAIL]

**Include:**
- Overall experience (1-5 stars)
- What worked well
- What needs improvement
- Would you recommend this tool? (Yes/No)

### Option 3: Form (Quick Feedback)
Fill out: [FEEDBACK_FORM_URL]

---

## Quick Start Guide

### Access the System
1. Click: [DEPLOYMENT_URL]
2. You'll see the FastAPI Swagger interface
3. Scroll down to see all available endpoints

### Try Your First Request
1. Find the endpoint `/api/v1/consult/direction`
2. Click "Try it out"
3. Fill in sample data:
   ```json
   {
     "direction": "north",
     "space_type": "bedroom",
     "query": "best practices for north-facing bedroom"
   }
   ```
4. Click "Execute"
5. See the response!

### Using cURL (Command Line)
```bash
curl -X POST [DEPLOYMENT_URL]/api/v1/consult/direction \
  -H "Content-Type: application/json" \
  -d '{
    "direction": "north",
    "space_type": "bedroom",
    "query": "best practices for north-facing bedroom"
  }'
```

---

## Sample Test Cases

### Test 1: Check System Health
```
Endpoint: GET /health
Expected: {"status": "operational", ...}
```

### Test 2: Get Direction Advice
```
Endpoint: POST /api/v1/consult/direction
Query: "What are best practices for a bedroom facing north?"
Expected: Detailed recommendations about north-facing bedrooms
```

### Test 3: Analyze Room
```
Endpoint: POST /api/v1/consult/room
Query: "How to optimize kitchen energy?"
Expected: Kitchen-specific Vastu recommendations
```

**See [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md) for all 20 tests.**

---

## Expected Behavior

✅ **Responses typically come back in 2-15 seconds**
- First request: 5-10 seconds (model loading)
- Subsequent: 2-5 seconds

✅ **All responses include detailed recommendations**
- Based on Vastu principles
- Practical and actionable
- Personalized to your query

✅ **The system handles edge cases gracefully**
- Invalid input gets clear error messages
- No crashes or 500 errors
- Informative responses

---

## Important Notes

🔒 **Privacy:** Your queries are sent to Anthropic (API provider) but NOT stored or used for training.

⚡ **Performance:** First user launch takes ~40 seconds as the system initializes. Subsequent requests are faster.

📊 **Reliability:** The system is designed to handle 20+ concurrent users. If you see slowness, it might be because others are testing simultaneously.

---

## Troubleshooting

### "Connection refused" or "Can't reach server"
- Wait 30-60 seconds and try again
- Space might be initializing
- If persistent, let us know!

### "500 Internal Server Error"
- Try a simpler query first
- Refresh the page and try again
- If it repeats, report with the error details

### "No response after 30 seconds"
- This is a timeout
- Try a shorter query
- If frequent, report the issue

---

## What Success Looks Like

✅ System health checks pass  
✅ Get meaningful responses for all queries  
✅ Responses feel accurate to Vastu principles  
✅ Response times are reasonable (< 15 seconds)  
✅ No crashes or confusing errors  
✅ Can handle multiple requests  

---

## Timeline

- **Today:** Click link and access system
- **Next 24-48 hours:** Run your 20 tests
- **By [DATE]:** Submit feedback
- **[DATE+1]:** System improvements based on feedback
- **[DATE+2]:** Full public release

---

## Questions?

📧 Email: [YOUR_EMAIL]  
💬 Chat: [CHAT_LINK_IF_AVAILABLE]  
🐛 Issues: [GITHUB_ISSUES_URL]  

---

## Thank You!

Your testing and feedback is crucial to making this tool better. We appreciate your time and input!

### Tester Recognition
If you'd like, we'll credit you in the public release as a beta tester.

---

## Quick Stats About Vastu Shastra DSS

- **Built with:** Claude AI, FastAPI, Python
- **Knowledge Base:** Classical Vastu texts and principles
- **Response Speed:** 2-15 seconds per query
- **Accuracy:** Trained on authentic Vastu principles
- **Scalability:** Handles 20+ concurrent users
- **Status:** Beta testing phase

---

## Remember

1. **Each test takes ~5 minutes on average**
2. **20 tests = ~2-3 hours total**
3. **You can do this over multiple days**
4. **We need your honest feedback**
5. **Errors and issues are valuable data!**

---

**Start Testing Now:** [DEPLOYMENT_URL]

**See Testing Guide:** [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)

---

**Thank you for helping us test the Vastu Shastra DSS!**

*Version: 1.0 | October 8, 2024*
