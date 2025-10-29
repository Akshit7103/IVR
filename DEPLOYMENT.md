# Deployment Guide - Render

This guide will walk you through deploying your IVR Fraud Detection system on Render.

## Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. A [GitHub account](https://github.com)
3. Your Twilio credentials (SID, Auth Token, Phone Number)
4. Git installed on your computer

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial commit - IVR Fraud Detection System"
```

### 1.2 Create a GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `ivr-fraud-detection`)
3. Don't initialize with README (you already have files)

### 1.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/ivr-fraud-detection.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

## Step 2: Deploy on Render

### 2.1 Connect GitHub to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** button
3. Select **"Web Service"**
4. Connect your GitHub account if not already connected
5. Select your `ivr-fraud-detection` repository

### 2.2 Configure the Web Service

Fill in the following details:

- **Name**: `ivr-fraud-detection` (or your preferred name)
- **Region**: Choose closest to you (e.g., Oregon)
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: `Free`

### 2.3 Add Environment Variables

Click **"Advanced"** and add these environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `TWILIO_SID` | `ACxxxxxxxxxx` | Your Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | `your_auth_token` | Your Twilio Auth Token |
| `TWILIO_NUMBER` | `+1234567890` | Your Twilio Phone Number |
| `FLASK_SECRET_KEY` | (auto-generated) | Click "Generate" button |
| `FLASK_ENV` | `production` | Sets production mode |
| `PYTHON_VERSION` | `3.11.0` | Python version |

**Important**: Keep your Twilio credentials secure. Never commit them to Git.

### 2.4 Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy your application
3. Wait for the deployment to complete (5-10 minutes)
4. You'll get a URL like: `https://ivr-fraud-detection-xxxx.onrender.com`

## Step 3: Update Twilio Webhooks

Your Render URL will be automatically available as `RENDER_EXTERNAL_URL` environment variable, and the app is configured to use it in production.

**Note**: The PUBLIC_URL is automatically set by Render, so you don't need to manually configure it in environment variables.

## Step 4: Test Your Deployment

1. Open your Render URL: `https://your-app-name.onrender.com`
2. You should see your IVR dashboard
3. Try triggering a call to test the system
4. Monitor logs in Render dashboard: **Logs** tab

## Step 5: Monitor and Maintain

### View Logs
- Go to your Render dashboard
- Click on your service
- Click **"Logs"** tab to see real-time logs

### Update Your App
```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically redeploy when you push to GitHub.

## Troubleshooting

### Issue: Calls not connecting

**Solution**:
- Check that environment variables are set correctly in Render
- Verify Twilio credentials are correct
- Check Render logs for errors

### Issue: "Application Error" on page load

**Solution**:
- Check Render logs for Python errors
- Verify all dependencies are in `requirements.txt`
- Ensure `data/transactions.json` exists in your repository

### Issue: Database/JSON file resets after deployment

**Solution**:
Render's free tier uses ephemeral storage. For persistent data:
1. Use Render's PostgreSQL database (requires code changes)
2. Use external storage like AWS S3
3. Accept that data resets on each deployment (for testing)

### Issue: App goes to sleep

**Solution**:
- Free tier apps sleep after 15 minutes of inactivity
- First request after sleep may take 30-60 seconds
- Upgrade to paid plan for always-on service
- Or use a service like [UptimeRobot](https://uptimerobot.com/) to ping your app every 5 minutes

## Production Recommendations

1. **Use PostgreSQL**: Replace JSON file with Render PostgreSQL for persistent data
2. **Environment Security**: Regularly rotate your Twilio credentials
3. **Monitoring**: Set up Render alerts for errors and downtime
4. **Custom Domain**: Add a custom domain in Render settings (paid feature)
5. **HTTPS**: Render provides free SSL certificates automatically
6. **Scaling**: Monitor usage and upgrade plan if needed

## Cost Information

- **Render Free Tier**: $0/month
  - 750 hours/month
  - Apps sleep after 15 min inactivity
  - 512 MB RAM
  - Shared CPU

- **Render Starter**: $7/month
  - Always on
  - 512 MB RAM
  - More reliable

## Support

- **Render Docs**: [https://render.com/docs](https://render.com/docs)
- **Twilio Support**: [https://support.twilio.com](https://support.twilio.com)
- **Application Issues**: Check Render logs first

## Quick Commands Reference

```bash
# View local logs
python app.py

# Commit and push changes
git add .
git commit -m "Your message"
git push origin main

# View git status
git status

# View git log
git log --oneline
```

---

## Deployment Checklist

- [ ] Git repository initialized
- [ ] Code pushed to GitHub
- [ ] Render web service created
- [ ] All environment variables configured
- [ ] Deployment successful
- [ ] Dashboard accessible via Render URL
- [ ] Test call completed successfully
- [ ] Twilio webhooks receiving requests
- [ ] Logs are clean (no errors)

**Your IVR Fraud Detection System is now live!** 🎉
