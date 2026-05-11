# Clarivise Scan — Quick Start Guide

**Version 1.0** | Last Updated: May 2026

---

## What is Clarivise Scan?

Clarivise Scan is a Chrome extension that sits inside Microsoft Outlook on the web. When you open an email and suspect it might be phishing, spam, or otherwise suspicious, you click **Analyze Email** and get back an AI-powered verdict in seconds — with plain-English explanations of any red flags.

**Key features:**
- ✅ Instant phishing and spam detection
- ✅ Link and attachment analysis
- ✅ Display name impersonation detection
- ✅ No extra apps or logins — works right in Outlook
- ✅ Send suspicious emails to IT Security for review
- ✅ Your email content is never stored or trained on

---

## Step 1: Install the Extension

### For Google Chrome

1. Open Chrome and go to the **Chrome Web Store**
2. Search for **"Clarivise Scan"** (or use the direct link provided by your administrator)
3. Click **Add to Chrome**
4. When prompted, click **Add extension** to confirm
5. The extension icon will appear in your Chrome toolbar

### For Microsoft Edge (Chromium)

1. Open Edge and go to the **Microsoft Edge Add-ons Store**
2. Search for **"Clarivise Scan"**
3. Click **Get**
4. Click **Add extension** to confirm
5. The extension icon will appear in your Edge toolbar

---

## Step 2: Configure Your Connection

1. Click the **Clarivise Scan extension icon** in your toolbar (📧)
2. A small popup will open — click the **⚙️ Connection** tab
3. You will see two fields:
   - **Proxy URL** — paste the proxy address provided by your administrator (e.g., `https://clarivise.example.com/analyze`)
   - **Extension Token** — paste your product key (a long alphanumeric string)
4. Click **Save**
5. You should see a green checkmark ✅ — you're connected!

**Where do I get these values?**
- Your **Extension Token** was provided when you signed up (shown once, copy it to a safe place)
- Your **Proxy URL** comes from your administrator or the signup email
- If you don't have these, contact your IT team or the Clarivise support team

---

## Step 3: Use Clarivise Scan

### Analyzing an Email

1. Open any email in **Outlook on the web**
2. In the sidebar (on the right), you'll see the Clarivise Scan panel
3. Click **Analyze Email**
4. Wait 2–5 seconds for the AI to process
5. You'll see:
   - **Phishing Score** — how likely the email is a phishing attempt (0–100)
   - **Spam Score** — how likely it's spam or unwanted (0–100)
   - **Verdict** — Safe, Suspicious, or Phishing
   - **Findings** — Plain-English explanation of any red flags (sender mismatch, suspicious links, etc.)

### What the Verdict Means

- **🟢 SAFE** — The email looks legitimate. It's probably okay to open links and download attachments
- **🟡 SUSPICIOUS** — Something seems off. Be cautious with links and downloads. Consider contacting the sender through a different channel to verify
- **🔴 PHISHING** — This email has strong phishing indicators. Do not click links or download attachments. Report to IT Security

### Send to Security for Review

If you think an email is suspicious or want IT to take a closer look:

1. Click **Send to IT Security** (or similar button in the panel)
2. A short form will pop up — add any comments you want IT to see
3. Click **Submit**
4. IT Security will review it and may take action (block sender, remove from inbox, etc.)

---

## Troubleshooting

### "Extension not connected" or "Invalid token"

**Problem:** The green checkmark isn't showing in the **Connection** tab.

**Solution:**
- Check that you pasted the **full Extension Token** correctly (no extra spaces)
- Check that the **Proxy URL** is correct and includes `https://`
- Ask your administrator to confirm the URL and token are still valid
- Your token may have expired — request a new one from your admin

### "No analyze button appears"

**Problem:** You don't see an **Analyze Email** button in the Outlook sidebar.

**Solution:**
- Make sure you're in **Outlook on the web** (outlook.office.com or your organization's custom URL)
- The extension only works in the web version, not the Outlook desktop app
- Refresh the page (Ctrl+R or Cmd+R)
- If the issue persists, reinstall the extension

### "Analyzing... takes too long"

**Problem:** The analysis spinner never stops or takes more than 30 seconds.

**Solution:**
- Check your internet connection
- The AI service may be temporarily slow — try again in a minute
- Contact IT or Clarivise support if the problem continues

### "I lost my Extension Token"

**Problem:** You closed the page where your token was shown and didn't copy it.

**Solution:**
- You cannot recover a lost token — tokens are shown only once for security
- Request a new token by going to the Clarivise signup portal (provided by your admin)
- Sign in with your work email and request a fresh key

---

## Best Practices

1. **Verify sender address** — Look at the full email address in the **From** line, not just the display name. Scammers often spoof familiar names
2. **Hover over links** — Before clicking, hover over any link to see the actual destination URL
3. **Watch for urgency** — Phishing emails often create artificial pressure ("Act now or your account will be locked!")
4. **Check for personal details** — Legitimate emails from your bank or IT usually address you by name and include specific account details. Generic greetings are a red flag
5. **Use Analyze Email for borderline cases** — Scan is a supplement to your own judgment, not a replacement. If something feels off, use Analyze Email

---

## Data Privacy

**Your email content is safe.**

- Clarivise Scan sends only the email headers, subject, body text, and link destinations to our secure analysis server
- We do **not** store full email bodies — only verdict metadata (score, verdict, findings)
- Your emails are **never** used to train any AI model
- Your data is processed in-memory and deleted immediately after analysis
- For details, see the **Privacy Policy** on the Clarivise portal

---

## Support

If you need help:

1. **Check this guide** — most issues are covered in **Troubleshooting** above
2. **Email your IT team** — they can verify your token, proxy URL, and connection
3. **Contact Clarivise support** — email **support@clarivise.example.com** with:
   - Your work email address
   - The error message you're seeing
   - What browser and OS you're using (Chrome/Edge, Windows/Mac)
   - Steps you took before the problem occurred

---

**Happy analyzing! 🎯**
