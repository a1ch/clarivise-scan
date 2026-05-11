# Clarivise — Frequently Asked Questions

**Version 1.0** | Last Updated: May 2026

---

## General

### Q: What is Clarivise?
**A:** Clarivise is a suite of AI-powered email security products for Microsoft 365. We have two products:
- **Clarivise Scan** — an on-demand extension for analyzing individual emails
- **Clarivise Shield** — automatic protection at the mail transport layer

### Q: Who makes Clarivise?
**A:** Clarivise is developed by Ingot Solutions. We use Claude AI (from Anthropic) for analysis and are committed to privacy-first design.

### Q: Is Clarivise safe?
**A:** Yes. Clarivise is built on two principles:
1. **Your data is yours** — we never store, train on, or share your emails
2. **Security first** — all data is processed server-side with encryption in transit

See the **Privacy Policy** for details.

---

## Clarivise Scan

### Q: How much does Clarivise Scan cost?
**A:** 
- **Trial:** Free for 15 days
- **Annual:** From $5 per user per month (billed annually)

Volume discounts are available. Contact sales@clarivise.io for enterprise pricing.

### Q: What browsers does Scan support?
**A:** Clarivise Scan works on:
- ✅ Google Chrome (recommended)
- ✅ Microsoft Edge (Chromium-based)
- ❌ Firefox (not currently supported)
- ❌ Safari (not currently supported)

### Q: Does Scan work with Outlook desktop (installed on my computer)?
**A:** No. Scan only works with **Outlook on the web** (accessed via browser at outlook.office.com or your organization's custom URL).

### Q: Can I use Scan on my personal Gmail or Yahoo account?
**A:** No. Scan is designed specifically for Microsoft 365 / Outlook on the web. It doesn't work with Gmail, Yahoo, or other email providers.

### Q: How long does analysis take?
**A:** Typically 2–5 seconds from clicking **Analyze Email** to receiving the verdict. Internet speed and server load may affect this.

### Q: What if I get a false positive (email marked SUSPICIOUS but it's actually legitimate)?
**A:** 
1. Review the **Findings** section — it explains why the email was flagged
2. Ask the sender to verify their email address (spoof detection is common for legitimate lookalike domains)
3. Check for common red flags: unusual sender, links you don't recognize, unsolicited attachments
4. If you're confident the email is safe, you can trust it — Scan is a supplement to your judgment, not a replacement
5. Consider adding the sender's domain to your IT admin's **Allowlist** in Shield (if used)

### Q: What information does Scan send to Clarivise servers?
**A:** When you click **Analyze Email**, we send:
- Email subject line, sender, and recipient
- Email body text (up to 3,000 characters)
- Hyperlink display text and actual destination domains
- Attachment file names
- Whether the sender is internal or external

**We do not send:** attachment contents, embedded images, or hidden email metadata.

### Q: Can I use the same product key on multiple computers?
**A:** Yes. One product key can be used on multiple browsers and devices. However, product keys are tied to individuals — don't share them with others.

### Q: What happens when my product key expires?
**A:** You'll see a warning in the extension popup. Contact your IT admin to request a new key. Keys are renewable annually.

---

## Clarivise Shield

### Q: How much does Clarivise Shield cost?
**A:** 
- From $12 per user per month (billed annually)
- Minimum 5 users per organization
- Volume discounts available

### Q: Does Shield require any changes to our email infrastructure?
**A:** Minimally. Shield works by adding a single **mail flow rule** in Microsoft 365. No hardware changes, no gateway replacement, no new servers required.

### Q: Can we use Shield alongside our existing email security tools?
**A:** Yes! Shield is designed to complement, not replace, existing email gateways and anti-malware tools. We work well with:
- Proofpoint, Mimecast, Cisco, Barracuda (existing email gateways)
- Microsoft Defender for Office 365
- SpamTitan, Fortinet, Sophos, Kaspersky

Tell us what you use and we'll help optimize the integration.

### Q: How long does it take to set up Shield?
**A:** About **30 minutes** for basic setup:
- 5 minutes: Sign up and get API credentials
- 10 minutes: Create the mail flow rule in Microsoft 365
- 5 minutes: Configure basic Shield settings (quarantine policy, allow/blocklist)
- 10 minutes: Monitor the admin dashboard

Advanced customization (custom rules, integration with other tools) may take longer.

### Q: What's the difference between hosted and self-hosted Shield?
**A:** 

| Aspect | Hosted | Self-Hosted |
|--------|--------|-------------|
| **Infrastructure** | Clarivise manages servers | You manage Azure resources |
| **Updates** | Automatic | You control the schedule |
| **Data location** | Clarivise data center | Your Azure subscription |
| **Cost** | Lower (shared infrastructure) | Higher (dedicated resources) |
| **Setup complexity** | Simple (5 minutes) | Complex (requires Azure knowledge) |
| **Best for** | Most organizations | Orgs with strict data residency requirements |

**Recommendation:** Start with **hosted**. If you later need self-hosted for compliance reasons, we can help migrate.

### Q: Does Shield work with on-premises Exchange?
**A:** Not currently. Shield requires **Exchange Online** (Microsoft 365). If you're running on-premises Exchange, contact us about alternative options.

### Q: What happens to emails that are marked PHISHING?
**A:** By default:
1. The email is moved to a quarantine folder (not the user's inbox)
2. The IT admin can review it in the Shield admin dashboard
3. The admin can release it to the inbox, delete it, or add the sender to a blocklist
4. After 30 days, quarantined emails are automatically deleted

Users can request release via quarantine notification email.

### Q: How does Shield handle false positives?
**A:** 
1. IT admin reviews the email in the admin dashboard
2. If it's legitimate, they can:
   - Release it to the user's inbox
   - Add the sender to the **Allowlist** so future emails are never flagged
3. Clarivise learns from feedback to improve accuracy over time

We aim for <1% false positive rate, but organization-specific tuning may be needed.

### Q: Can users bypass Shield or release their own emails?
**A:** By default, no — only IT admins can manage quarantine. However, you can configure:
- User-initiated **quarantine notification emails** that include a one-time link to request release
- Self-service quarantine portal where users can see their own quarantined emails

### Q: Does Shield scan internal emails?
**A:** By default, no — the mail flow rule only analyzes **external** senders (outside your organization). This is intentional: Shield protects against external threats.

If you want to scan internal emails too, contact Clarivise support for custom configuration.

### Q: What's the SLA for Shield uptime?
**A:** **Hosted Shield:** 99.5% uptime SLA (details in your service agreement).

**Self-hosted Shield:** SLA is based on your Azure infrastructure and maintenance practices.

---

## Data & Privacy

### Q: Where is my email data stored?
**A:** 
- **Clarivise Scan:** Email metadata (sender, subject, verdict) is logged in the Clarivise database for 90 days
- **Shield:** Same as Scan, plus additional metadata about mail flow actions
- **Full email body:** Never stored. It's processed in-memory and discarded immediately

### Q: How long do you keep my data?
**A:** 
- Scan logs: 90 days
- Shield scan logs: 90 days
- Shield quarantine: 30 days
- Then permanently deleted

You can request earlier deletion by contacting support.

### Q: Is my email data encrypted?
**A:** Yes:
- **In transit:** All data sent to Clarivise is encrypted with TLS 1.3
- **At rest:** Data in our database is encrypted with AES-256
- **In memory:** Email content is never written to disk — only kept in RAM during analysis

### Q: Do you train AI models on my emails?
**A:** Absolutely not. Clarivise (and Claude AI) never use customer emails for training. This is contractually guaranteed.

### Q: Can Clarivise see my emails?
**A:** Technically, Clarivise systems process your email content to analyze it. But:
- **No human access** — no Clarivise employee can read your emails
- **Encrypted isolation** — your data is encrypted at rest and in transit
- **No logging of content** — only verdict metadata is logged
- **No third-party access** — we don't sell or share email data

If you have additional privacy concerns, we can sign a Data Processing Agreement (DPA).

### Q: Does Clarivise comply with GDPR, HIPAA, SOC 2?
**A:** 
- ✅ **GDPR** — Yes (EU data residency available)
- ✅ **SOC 2 Type II** — Certified
- ❓ **HIPAA** — Not currently, but in progress. Contact us if you need this
- ❓ **PCI DSS** — Not currently certified

See the full **Privacy Policy** and **Terms and Conditions** for details.

---

## Technical

### Q: What is Claude AI?
**A:** Claude is an AI assistant made by Anthropic. Clarivise uses Claude to analyze email for phishing, spam, and other threats. Claude is known for being thoughtful, nuanced, and safe.

### Q: Why Claude and not ChatGPT or Gemini?
**A:** We chose Claude because:
- **Privacy:** Claude doesn't train on user inputs by default
- **Accuracy:** Claude is excellent at nuanced security analysis
- **Safety:** Anthropic is aligned with our values on data protection

### Q: What happens if the Claude AI API is down?
**A:** 
- **Scan:** If the API is unavailable, you get an error message. Retry in a few seconds
- **Shield:** If the API is unavailable, emails bypass analysis and are delivered normally (fail-safe behavior)

This ensures email flow is never interrupted by AI service outages.

### Q: Can I use my own API key instead of yours?
**A:** 
- **Scan:** No, the proxy URL handles authentication
- **Shield (self-hosted):** Yes, you provide your own Anthropic API key in Azure Key Vault

### Q: Does Clarivise work with Microsoft Graph API?
**A:** 
- **Scan:** No, it's a Chrome extension that reads Outlook on the web directly
- **Shield:** Yes, it integrates with Exchange Online mail flow rules (part of Microsoft 365 API)

### Q: Can I integrate Clarivise with Zapier, Power Automate, or other automation tools?
**A:** 
- **Shield admin dashboard:** Can export scan logs and quarantine data (CSV/JSON)
- **Webhooks:** Contact Clarivise support for custom webhook integrations
- **Power Automate:** Coming soon (notify alerts via Teams, Slack, etc.)

---

## Support & Billing

### Q: How do I contact support?
**A:** 
- **Email:** support@clarivise.io
- **Response time:** 24 hours (business days)
- **Chat:** Available in the admin dashboard for paid customers

### Q: Can I cancel my subscription?
**A:** Yes. Annual subscriptions can be cancelled with 30 days' notice. Monthly subscriptions can be cancelled anytime.

### Q: Is there a refund policy?
**A:** Yes — 30-day money-back guarantee if you're not satisfied. Contact support to request a refund.

### Q: Do you offer free trials?
**A:** 
- **Scan:** 15-day free trial (requires signup)
- **Shield:** 30-day free trial (requires setup of mail flow rule)

No credit card required for trials.

### Q: Can I upgrade or downgrade my plan?
**A:** Yes. Changes take effect at the next billing cycle. Contact sales@clarivise.io for custom plans.

---

## Still have questions?

**Email us:** support@clarivise.io  
**Chat:** Available in the Scan extension and Shield admin dashboard  
**Schedule a call:** https://calendly.com/clarivise/support

---

**Happy analyzing! 🎯**
