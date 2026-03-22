# Privacy Policy — Outlook Email Evaluator

**Last updated: March 22, 2026**

## Overview

Outlook Email Evaluator is a Chrome extension that analyzes emails in Microsoft Outlook Web for spam and phishing threats using the Anthropic Claude AI API. This privacy policy explains what data is collected, how it is used, and how it is protected.

## Data Collected

When you use the Analyze Email feature, the following information is extracted from the currently open email and sent to the Anthropic API:

- Email subject line
- Sender display name
- Email body text (up to 3,000 characters)
- Hyperlink display text and destination domains extracted from the email body

No other data is collected or transmitted.

## How Your Data Is Used

Email content is sent solely to the Anthropic API (api.anthropic.com) for the purpose of analyzing the email for spam and phishing indicators. The analysis result is returned to your browser and displayed in the extension sidebar. No data is stored, logged, or shared by this extension beyond what is processed by the Anthropic API.

## Anthropic API

This extension uses the Anthropic Claude API to perform email analysis. Your use of this extension is subject to [Anthropic's Privacy Policy](https://www.anthropic.com/privacy) and [Terms of Service](https://www.anthropic.com/terms). Anthropic may process and retain data submitted to their API in accordance with their policies.

## API Key Storage

Your Anthropic API key is stored locally in your browser using Chrome's `chrome.storage.local` API. It is never transmitted to any server other than the Anthropic API, and only for the purpose of authenticating API requests. It is not accessible to any website or third party.

## Settings Storage

Your configured organization domain and any custom instructions entered in the Settings tab are stored locally in your browser using Chrome's `chrome.storage.local` API. This data never leaves your device except as part of the prompt sent to the Anthropic API.

## Email Content

Email content is processed transiently — it is read from the page, sent to the Anthropic API, and the result is displayed. This extension does not store, log, cache, or transmit email content to any server other than the Anthropic API.

## Permissions Used

This extension requests the following Chrome permissions:

- **activeTab** — to read the content of the Outlook tab you are currently viewing
- **storage** — to store your API key and settings locally in your browser
- **Host permission for outlook.cloud.microsoft and outlook.office.com** — to inject the sidebar UI into Outlook Web
- **Host permission for api.anthropic.com** — to send analysis requests to the Anthropic API

## Data Sharing

This extension does not sell, share, or disclose any user data to any third party other than the Anthropic API for the sole purpose of performing email analysis as requested by the user.

## Children's Privacy

This extension is not directed at children under the age of 13 and does not knowingly collect data from children.

## Changes to This Policy

This privacy policy may be updated periodically. The date at the top of this document reflects the most recent revision. Continued use of the extension after changes constitutes acceptance of the updated policy.

## Contact

For questions about this privacy policy, please open an issue at:
https://github.com/a1ch/outlook-email-evaluator
