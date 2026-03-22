# Outlook Email Evaluator

A Chrome extension that uses Claude AI to analyze emails in Outlook Web (outlook.cloud.microsoft) for spam and phishing threats.

## Features

- **AI-powered analysis** using Claude claude-sonnet-4-20250514 via the Anthropic API
- **Spam & phishing detection** with risk scores and detailed reasoning
- **Link revelation** — automatically shows real destination domains next to hyperlinks, decoding Outlook safelinks
- **Domain mismatch detection** — flags links where display text shows a different domain than the actual destination
- **External sender detection** — uses Outlook's own external organization warning as ground truth
- **Zero trust approach** — no domain whitelisting, every email analyzed on content regardless of sender
- **Out-of-band verification reminders** for high-risk requests (access changes, payments, credential requests)
- **Collapsible sidebar** that minimizes to a tab on the right edge
- **Configurable settings** — set your org domain and custom instructions without redeploying

## Installation (Developer Mode)

1. Download or clone this repository
2. Open Chrome and go to `chrome://extensions`
3. Enable **Developer Mode** (top right toggle)
4. Click **Load unpacked**
5. Select the `outlook-evaluator` folder
6. Click the extension icon → **API Key** tab → enter your [Anthropic API key](https://console.anthropic.com) → Save
7. Click **Settings** tab → enter your organization domain (e.g. `yourcompany.com`) → Save
8. Navigate to `outlook.cloud.microsoft` and reload the page

## Usage

1. Open any email in Outlook Web
2. The sidebar appears on the right — click **Analyze Email**
3. Results show:
   - **Verdict** (Safe / Suspicious / Spam / Phishing)
   - **Phishing risk score** and **spam score**
   - **Summary** of findings
   - **Why it's suspicious** — specific red flags found
   - **Links** — all hyperlinks with real destinations revealed
   - **Suggested action**

## Configuration

Click the extension icon to access settings:

- **API Key** — your Anthropic API key (stored locally, never transmitted except to Anthropic)
- **Settings**
  - *Organization Domain* — used to identify external vs internal senders (e.g. `yourcompany.com`)
  - *Additional Instructions* — custom guidance for the AI analyzer, takes effect immediately without redeploying

## Privacy

- Email content is sent to the Anthropic API for analysis
- Your API key is stored locally in Chrome's extension storage
- No data is stored or logged beyond what Anthropic's API processes

## Requirements

- Google Chrome
- Anthropic API key ([get one here](https://console.anthropic.com))
- Access to Outlook Web at `outlook.cloud.microsoft`

## Chrome Web Store

Coming soon.

## License

MIT
