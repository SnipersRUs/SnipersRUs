# SRUS Scanner - Deployment Guide

Complete guide to deploying your SnipersRUs website to GitHub Pages.

## 📋 Prerequisites
- GitHub Desktop app installed
- Cursor IDE
- GitHub account
- SnipersRUs repository

---

## 🚀 Step-by-Step Deployment

### Step 1: Final Testing in Cursor

1. **Open files in Cursor:**
   ```
   /Users/bishop/Documents/GitHub/SnipersRUs/index.html
   /Users/bishop/Documents/GitHub/SnipersRUs/landing.html
   /Users/bishop/Documents/GitHub/SnipersRUs/login.html
   /Users/bishop/Documents/GitHub/SnipersRUs/scanner.html
   ```

2. **Test the website:**
   - Open `index.html` in your browser
   - Verify all sections load correctly
   - Test the live scanner updates
   - Check responsive design on mobile

3. **Make any final adjustments** in Cursor before deploying.

---

### Step 2: Commit Changes in Cursor

1. **Check current status:**
   In Cursor terminal:
   ```bash
   git status
   ```

2. **Stage all files:**
   ```bash
   git add .
   ```

3. **Create a commit:**
   ```bash
   git commit -m "Deploy SRUS Scanner with live homepage

   - Updated index.html as main SnipersRUs landing page
   - Added live BTC scanner with support/resistance
   - Real-time market info panel (trend, volume, GPS, divergence)
   - Active trades display
   - 3 Laws of Sniping section
   - CTA to join Discord community
   - Responsive design"
   ```

4. **View your commits:**
   ```bash
   git log --oneline -5
   ```

---

### Step 3: Push to GitHub Using GitHub Desktop

#### Option A: Via GitHub Desktop App (Recommended)

1. **Open GitHub Desktop:**
   - You should see your SnipersRUs repository
   - You'll see your recent commits listed

2. **Verify your commit appears:**
   - Check the commit message you created
   - Review changed files list

3. **Push to main branch:**
   - Click the "Publish repository" button (if first time)
   - Or click "Push origin" to push existing changes

4. **Wait for push to complete:**
   - You'll see a green checkmark when done
   - The changes are now on GitHub

#### Option B: Via Terminal/Cursor

If you prefer command line:
```bash
git push origin main
```

---

### Step 4: Enable GitHub Pages

1. **Go to your repository on GitHub:**
   - Visit: https://github.com/your-username/SnipersRUs

2. **Navigate to Settings:**
   - Click "Settings" tab at top
   - Scroll down to "Pages" section (in left sidebar)

3. **Configure Pages:**
   - Under "Source", select: **Deploy from a branch**
   - Select branch: **main**
   - Select folder: **/(root)**
   - Click "Save"

4. **Wait for deployment:**
   - GitHub will take 1-2 minutes to deploy
   - You'll see a checkmark when ready

5. **Get your live URL:**
   - Your site will be at: `https://your-username.github.io/SnipersRUs/`

---

### Step 5: Verify Deployment

1. **Visit your live site:**
   ```
   https://your-username.github.io/SnipersRUs/
   ```

2. **Test all features:**
   - ✅ Live BTC scanner updating every 3 seconds
   - ✅ Support/Resistance lines visible on chart
   - ✅ Market info panel showing trend, volume, GPS, divergence
   - ✅ Active trades section displaying
   - ✅ 3 Laws of Sniping section
   - ✅ Discord CTA button working
   - ✅ Mobile responsive design

3. **Check browser console for errors:**
   - Press F12 or Cmd+Option+I
   - Go to "Console" tab
   - Ensure no JavaScript errors

---

## 🔄 Updating Your Site (Future Changes)

### When you want to make updates:

1. **Edit files in Cursor**
2. **Test locally** (open HTML in browser)
3. **Commit changes in Cursor:**
   ```bash
   git add .
   git commit -m "Your commit message"
   ```
4. **Push via GitHub Desktop** or:
   ```bash
   git push origin main
   ```
5. **Wait 1-2 minutes** - GitHub Pages auto-deploys!

---

## 📁 File Structure

```
SnipersRUs/
├── index.html              # Main landing page (NEW - this replaces old scanner)
├── landing.html           # Subscription tier page (alternative)
├── login.html             # Login page (for future auth)
├── scanner.html            # Full-featured scanner dashboard
├── DEPLOYMENT_GUIDE.md    # This file
├── start_srus_scanner.sh  # Startup script
└── .gitignore             # Files to exclude from git
```

---

## 🎨 Features of New Index.html

### Live Homepage Scanner
- **Mini chart** showing BTC price with golden line
- **Support line** (green, dashed)
- **Resistance line** (red, dashed)
- **Updates every 3 seconds** (realistic, not chaotic)

### Market Info Panel
- **Trend**: BULLISH / BEARISH / NEUTRAL
- **Support Level**: Dynamic calculation
- **Resistance Level**: Dynamic calculation
- **Volume Status**: NORMAL / HIGH (3x)
- **GPS Status**: WATCHING / ACTIVE
- **Divergence Status**: NONE / DETECTED
- **Confluence Score**: 0/3 to 3/3 Laws

### Active Trades Section
- Shows open/pending trades
- Entry, Target, Stop Loss
- Real-time PnL updates
- Risk/Reward ratios

### 3 Laws Section
- Spiderline Confirmation
- Divergence Confirmation
- Volume Confirmation

### Call-to-Action
- Join Discord button
- Social links (TradingView, YouTube, Twitter)

---

## 🔧 Troubleshooting

### Issue: Changes not appearing on live site
**Solution:**
- Wait 1-2 minutes after pushing
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Clear browser cache

### Issue: GitHub Desktop won't push
**Solution:**
- Check internet connection
- Verify you're logged into GitHub Desktop
- Click "Fetch origin" first
- Try pushing from terminal instead

### Issue: Page shows 404
**Solution:**
- Verify Pages is enabled in repo Settings
- Check you're pushing to the right branch (main)
- Ensure index.html is in root of repository

### Issue: Live scanner not updating
**Solution:**
- Check browser console for JavaScript errors
- Verify you're on https:// (not http://)
- Clear browser cache

---

## 📱 Testing Checklist

Before going public, test:

- [ ] Homepage loads in Chrome
- [ ] Homepage loads in Safari
- [ ] Homepage loads in Firefox
- [ ] Mobile view works (phone)
- [ ] Tablet view works (iPad)
- [ ] Live scanner updates
- [ ] Support/resistance lines visible
- [ ] Market info panel updates
- [ ] Discord link opens correctly
- [ ] TradingView link opens correctly
- [ ] No console errors
- [ ] Images load (if any)
- [ ] All text is readable

---

## 🚀 Going Live

Once everything is tested and working:

1. **Push final commit:**
   ```bash
   git add .
   git commit -m "Final deployment - ready for public"
   git push origin main
   ```

2. **Wait for GitHub Pages deployment**

3. **Share your URL:**
   ```
   https://your-username.github.io/SnipersRUs/
   ```

4. **Announce on Discord!**

---

## 📞 Support

If you need help:
- Check GitHub documentation: https://docs.github.com/pages
- Review this guide again
- Ask community on Discord

---

## ✨ Next Steps

After deployment, consider adding:
- Real API integration for live BTC price
- User authentication system
- Database for trade tracking
- Email notifications for signals
- More interactive features

---

**Happy Trading! 🎯**
