# Clarivise Shield — Hosted Deployment

**Version 1.0** | Last Updated: May 2026

*For organizations using Clarivise Shield on our secure servers*

---

## Overview

Clarivise Shield is an automatic email security layer that sits between your mail gateway and your users' inboxes. Every inbound external email is analyzed by Claude AI, scored for phishing/spam/BEC risk, and automatically:

- ✅ Delivered normally if **SAFE**
- ⚠️ Tagged in the subject line if **SUSPICIOUS**
- 🔴 Quarantined if **PHISHING**

**Hosted deployment** means we manage the servers, AI, and infrastructure. You just set up a mail flow rule in Microsoft 365 and we handle the rest.

---

## Prerequisites

Before starting, ensure:

1. ✅ Your organization uses **Microsoft 365** (Exchange Online)
2. ✅ You have **admin rights** in the Microsoft 365 admin center
3. ✅ You've purchased or started a trial of **Clarivise Shield**
4. ✅ You have the **Shield proxy URL** (provided by Clarivise during onboarding)

---

## Step 1: Get Your Shield Configuration

When you signed up for Shield, Clarivise sent you an email with:

- **Shield Proxy URL** — the secure endpoint that analyzes email (e.g., `https://shield.clarivise.io/analyze-hosted`)
- **Organization ID** — your unique identifier in our system (e.g., `org-abc123xyz`)
- **Shield API Key** — a secret key used to authenticate requests
- **Admin Dashboard URL** — where you can see scan logs and manage quarantines (e.g., `https://shield.clarivise.io/dashboard`)

**Keep these values safe.** If you've misplaced them, contact Clarivise support.

---

## Step 2: Create a Mail Flow Rule

Shield works by routing a copy of every inbound external email to our analysis service before it reaches any inbox.

### In the Microsoft 365 admin center:

1. Go to **Exchange admin center** (https://admin.exchange.microsoft.com)
2. Click **Mail flow** > **Rules**
3. Click **+ New rule** and choose **Create a new rule**
4. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Clarivise Shield — Inbound Analysis` |
   | **Apply this rule if** | Select **The sender is located in** > **Outside the organization** |
   | **Do the following** | Select **Redirect the message to** |
   | **Select address** | Enter the Shield proxy URL (e.g., `shield@clarivise.io`) **OR** use **Redirect to host** and enter your proxy URL |

   *Note: The exact setup depends on your Shield deployment. Clarivise will provide a mail flow rule template during onboarding.*

5. Click **Save** 

The rule is now active. Emails start flowing to Shield for analysis.

---

## Step 3: Configure Shield Settings (Optional)

Log in to your **Admin Dashboard** (URL provided at signup) to customize:

### Quarantine Policies

- **Phishing emails** — automatically quarantine? (recommended: Yes)
- **Suspicious emails** — quarantine or tag? (recommended: tag with `[SUSPICIOUS]`)
- **Safe emails** — deliver normally (always Yes)

### Allow/Blocklist

- **Trusted senders** — emails from these domains/senders are always marked SAFE and bypass analysis
- **Blocked senders** — emails from these are always quarantined

### Notification Settings

- **Daily summary email** — IT receives a report of all verdicts, threat counts, and quarantined senders
- **Quarantine alerts** — notify admins immediately when phishing is detected

### Custom Rules

- Add organization-specific rules (e.g., "emails from trusted partner domain should always be SAFE")
- Define which email headers or content patterns should trigger extra scrutiny

---

## Step 4: Monitor the Dashboard

Your **Admin Dashboard** shows:

### Real-Time Overview
- **Emails analyzed today** — count of all inbound emails processed
- **Threats detected** — count of PHISHING and SUSPICIOUS verdicts
- **Quarantine queue** — emails pending admin review

### Scan Log
- Full table of recent emails with sender, subject, verdict, and score
- Search and filter by sender, subject, date range, verdict
- Click any email to see the detailed AI analysis (findings, flags, score breakdown)

### Quarantine Management
- Review quarantined emails
- Release to inbox, delete, or add sender to allowlist
- Export quarantine log for compliance/audit

### Reports
- Weekly threat summary (verdicts, top senders, attack patterns)
- Monthly compliance report (scan volume, threat density, response times)

---

## Troubleshooting

### "Emails are taking longer to arrive"

**Problem:** Users notice a delay between when emails are sent and when they arrive.

**Explanation:** Shield adds ~2–5 seconds to email delivery while analysis happens. This is normal.

**Solution:**
- If delays exceed 10 seconds, check the Dashboard **Health** tab
- Contact Clarivise support if you see performance alerts

### "All emails are marked SUSPICIOUS or PHISHING"

**Problem:** Too many false positives.

**Solution:**
- Check your **Quarantine Policies** — you may have settings that are too strict
- Review the **Admin Dashboard findings** for the flagged emails — do the red flags make sense?
- Add trusted sender domains to the **Allowlist** so legitimate email is never flagged
- Contact Clarivise support to tune the AI thresholds for your organization

### "Some emails bypass Shield analysis"

**Problem:** Internal emails or specific senders don't appear in the scan log.

**Explanation:** The mail flow rule only analyzes **external** senders (outside your organization). Internal emails skip Shield by design.

**Solution:**
- This is correct behavior — Shield protects against external threats
- If you want to analyze internal mail, contact Clarivise about custom rules

### "Users can't release quarantined emails"

**Problem:** Users receive a quarantine notification but can't click through to release or review the email.

**Solution:**
- Check that the **quarantine notification email** includes a link to the Clarivise user quarantine portal
- Make sure users' IT policies don't block access to the Clarivise domain
- Contact Clarivise support to verify the quarantine portal is deployed

---

## Data and Privacy

- **Email content:** Full message body is analyzed server-side but never stored on disk
- **Metadata stored:** Sender, recipient, subject, verdict, score, timestamp are logged for your dashboard
- **Never trained on:** Your email content is never used to train any AI model
- **Retention:** Scan logs are kept for 90 days for compliance and debugging; then permanently deleted
- **Your data is yours:** We never share, sell, or disclose email data to third parties

See the full **Privacy Policy** at **https://clarivise.io/privacy**

---

## FAQs

**Q: Can I turn off Shield for certain users?**
A: Yes. Create mail flow rules with specific conditions (e.g., "apply this rule to all except the Finance team"). Contact Clarivise support for help configuring user exemptions.

**Q: What happens to quarantined emails?**
A: They stay in quarantine for 30 days (configurable). After that, they're automatically deleted. You can manually release or delete them sooner from the Admin Dashboard.

**Q: Does Shield work with on-premises Exchange?**
A: No, Shield requires Exchange Online (Microsoft 365). On-premises Exchange deployments require a different setup — contact Clarivise for options.

**Q: Can I integrate Shield with other email security tools?**
A: Yes. Shield is designed to complement existing email gateways and anti-malware tools. Let us know what else you're using, and we'll help optimize the integration.

**Q: What SLA does Clarivise offer for Shield?**
A: Hosted Shield is backed by a **99.5% uptime SLA**. Details are in your service agreement.

---

## Support & Escalation

For help:

1. **Check this guide** — covers most common setup and troubleshooting questions
2. **Review the Admin Dashboard** — the **Health** tab shows system status and any active alerts
3. **Email Clarivise support** — support@clarivise.io with:
   - Your **Organization ID**
   - Description of the issue
   - Screenshots if applicable
   - Recent scan log data (export from Dashboard)

---

**Ready to get started? Set up the mail flow rule in Step 2 above, then monitor the Admin Dashboard!** 🛡️
