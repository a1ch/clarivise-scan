// Outlook Email Evaluator - Content Script

let sidebar = null;
let lastEmailId = null;
let observer = null;

// ─── Sidebar Injection ───────────────────────────────────────────────────────

function createSidebar() {
  if (document.getElementById('oe-sidebar')) return;

  sidebar = document.createElement('div');
  sidebar.id = 'oe-sidebar';
  sidebar.innerHTML = `
    <div id="oe-tab">
      <span id="oe-tab-icon">📧</span>
      <span>EVALUATOR</span>
    </div>
    <div id="oe-header">
      <span id="oe-title">📧 Email Evaluator</span>
      <button id="oe-close" title="Minimize">⟩</button>
    </div>
    <div id="oe-body">
      <div id="oe-idle">
        <p>Select or open an email to analyze it.</p>
      </div>
    </div>
    <div id="oe-footer">
      <button id="oe-analyze-btn" style="display:none">🔍 Analyze Email</button>
    </div>
  `;
  document.body.appendChild(sidebar);

  document.getElementById('oe-close').addEventListener('click', () => {
    sidebar.classList.add('oe-collapsed');
  });

  document.getElementById('oe-tab').addEventListener('click', () => {
    sidebar.classList.remove('oe-collapsed');
  });

  document.getElementById('oe-analyze-btn').addEventListener('click', () => {
    analyzeCurrentEmail();
  });
}

// ─── Email Extraction ────────────────────────────────────────────────────────

function findText(selectorList) {
  for (const sel of selectorList) {
    try {
      const el = document.querySelector(sel);
      if (el && el.innerText && el.innerText.trim().length > 0) {
        return el.innerText.trim();
      }
    } catch(e) {}
  }
  return null;
}

function getReadingPane() {
  // Find the reading pane container - scope all selectors to this
  const candidates = [
    document.querySelector('[aria-label="Reading Pane"]'),
    document.querySelector('[aria-label="reading pane"]'),
    document.querySelector('[class*="ReadingPane"]'),
    document.querySelector('[class*="readingPane"]'),
    document.querySelector('[data-testid="reading-pane"]'),
  ];
  return candidates.find(el => el !== null) || document.body;
}

function findTextIn(container, selectorList) {
  for (const sel of selectorList) {
    try {
      const el = container.querySelector(sel);
      if (el && el.innerText && el.innerText.trim().length > 0) {
        return el.innerText.trim();
      }
    } catch(e) {}
  }
  return null;
}

function extractEmail() {
  const pane = getReadingPane();

  // ── Subject ── scoped to reading pane only
  const subject = findTextIn(pane, [
    '[data-testid="subject"]',
    '[aria-label="Message subject"]',
    'h1',
    'h2',
    '[role="heading"]',
    '[class*="subject" i]',
  ]) || '(No subject found)';

  // ── Sender ── extract from button aria-label which contains full email
  let sender = '(No sender found)';
  const fromBtn = pane.querySelector('button[aria-label*="From:"]') ||
                  pane.querySelector('[aria-label*="From:"]');
  if (fromBtn) {
    // aria-label format is "From: Name <email>" or "From: Name, Online"
    const label = fromBtn.getAttribute('aria-label') || '';
    sender = label.replace(/^From:\s*/i, '').trim();
  }
  if (sender === '(No sender found)') {
    sender = findTextIn(pane, [
      '[data-testid="senderName"]',
      '[class*="sender" i]',
      '[class*="Sender"]',
      '[class*="Persona"] [class*="primaryText"]',
    ]) || '(No sender found)';
  }

  // ── Body ── scoped to reading pane only
  const body = findTextIn(pane, [
    '[aria-label="Message body"]',
    '[data-testid="message-body"]',
    'div[class*="UniqueMessageBody"]',
    '[id*="UniqueMessageBody"]',
    'div[class*="messageBody" i]',
    '[class*="body" i]',
  ]) || '(No body found)';

  // ── Extract hyperlinks: display text vs actual href ──────────────────────
  const links = [];
  // Use the already-scoped reading pane for link extraction
  let bodyEl = pane.querySelector('[aria-label="Message body"]') ||
               pane.querySelector('div[class*="UniqueMessageBody"]') ||
               pane.querySelector('[id*="UniqueMessageBody"]') ||
               pane.querySelector('div[class*="messageBody" i]') ||
               pane;

  if (bodyEl) {
    const anchors = bodyEl.querySelectorAll('a[href]');
    const seen = new Set();
    anchors.forEach(a => {
      try {
        const displayText = a.innerText.trim();
        let href = a.getAttribute('href') || '';

        // Decode Outlook safelinks wrapper to get real URL
        if (href.includes('safelinks.protection.outlook.com')) {
          try {
            const urlParam = new URL(href).searchParams.get('url');
            if (urlParam) href = decodeURIComponent(urlParam);
          } catch(e) {}
        }

        if (!href || href.startsWith('mailto:') || href.startsWith('#') || href.length < 10) return;

        let hrefDomain = '';
        try { hrefDomain = new URL(href).hostname.toLowerCase(); }
        catch(e) { hrefDomain = href.slice(0, 60); }

        if (seen.has(hrefDomain)) return;
        seen.add(hrefDomain);

        // Check if display text itself looks like a URL with a different domain
        let displayDomain = '';
        const urlPattern = displayText.match(/(?:https?:\/\/|www\.)([\w.-]+)/i);
        if (urlPattern) {
          try {
            const normalized = displayText.startsWith('http') ? displayText : 'https://' + displayText;
            displayDomain = new URL(normalized).hostname.toLowerCase();
          } catch(e) { displayDomain = urlPattern[1].toLowerCase(); }
        }

        const mismatch = displayDomain && hrefDomain &&
          !hrefDomain.includes(displayDomain.replace(/^www\./, '')) &&
          !displayDomain.includes(hrefDomain.replace(/^www\./, ''));

        links.push({
          display: displayText.slice(0, 80) || '(no text)',
          href: hrefDomain,
          mismatch
        });
      } catch(e) {}
    });
  }

  return {
    subject,
    sender,
    body: body.slice(0, 3000),
    links: links.slice(0, 20)
  };
}

// ─── Analysis ────────────────────────────────────────────────────────────────

async function analyzeCurrentEmail() {
  const email = extractEmail();
  setLoading();

  const now = new Date();
  const utcString = now.toUTCString();
  const localString = now.toLocaleString('en-US', { timeZone: 'America/Edmonton', timeZoneName: 'short' });

  // tenantDomain and customPrompt will be injected by background worker
  // Use placeholders here - background.js replaces them before sending to API
  const tenantDomain = '__TENANT_DOMAIN__';
  const customPrompt = '__CUSTOM_PROMPT__';

  // Check if Outlook shows external org warning - use targeted selectors only, no full DOM scan
  const paneForExternal = getReadingPane();
  const externalWarningEl = paneForExternal.querySelector('[class*="externalSender" i]') ||
    paneForExternal.querySelector('[class*="ExternalSender"]') ||
    paneForExternal.querySelector('[class*="external-sender" i]') ||
    paneForExternal.querySelector('[data-testid*="external" i]');
  // Also check the reading pane text for the standard Outlook external warning bar
  const externalBannerText = paneForExternal.querySelector('[role="alert"]')?.innerText || '';
  const isOutlookExternal = !!externalWarningEl || externalBannerText.toLowerCase().includes('external organization');

  const prompt = `You are a cybersecurity expert specializing in email threat analysis. Analyze the following email and respond ONLY with a JSON object — no markdown, no explanation outside the JSON.

IMPORTANT CONTEXT:
- Current date/time: ${utcString} (UTC) / ${localString} (Mountain Time). Do not flag dates as suspicious if they fall within the current day across timezones.
- Recipient organization domain: __TENANT_DOMAIN__
- Sender display name: ${email.sender} (this may be a display name only - look for the actual email address in the body or signature to determine if sender is internal or external)
- If you find sender email in the body/signature, check if it ends with __TENANT_DOMAIN__ to determine internal vs external
- Outlook external warning present: ${isOutlookExternal ? "YES - Microsoft has flagged this as from an external organization. You MUST include this in your reasons." : "NO - Microsoft has NOT flagged this as external, treat sender as internal unless proven otherwise by an email address in the body/signature"}
- Do NOT assume external based on display name alone. Only flag as external if Outlook says so OR if you find an external email address in the body/signature
__CUSTOM_PROMPT__

KEY RULES:
1. NEVER give any email a free pass based on sender domain alone - even internal senders or Microsoft itself can be compromised.
2. Only flag if sender is external to the recipient org if you can confirm this from an email address found in the body or signature. Never assume external from display name alone.
3. Links to __TENANT_DOMAIN__ or sharepoint.com subdomains of __TENANT_DOMAIN__ (e.g. streamflogroup.sharepoint.com) are INTERNAL links - do NOT flag them as suspicious.
3. A well-known domain (microsoft.com etc) means don't flag the domain - but DO still flag suspicious content, urgency, requests for credentials, unusual links, etc. The domain streamflogroup.sharepoint.com is the recipient organization's own internal SharePoint - NEVER flag it as suspicious or credential harvesting.
4. Analyze the email content and intent independently of who sent it.
5. Links to __TENANT_DOMAIN__ subdomains (e.g. streamflogroup.sharepoint.com) are INTERNAL links and must NOT be flagged as suspicious.
6. The recipient of this email is Shawn Stubbs. Do not confuse the recipient with the sender. "Hi Shawn" means Shawn is the recipient, not the sender.
5. If the email involves ANY of the following, the suggested_action MUST include the note "⚠️ Verify this request through official channels other than email (phone, in-person, or ticketing system) before taking action.": adding users or guest accounts, granting system access or permissions, approving payments or wire transfers, changing credentials or passwords, installing software, clicking links to login pages, or any urgent request requiring immediate action.

Email details:
Subject: ${email.subject}
From: ${email.sender}
Body:
${email.body}

Note: If body content is limited (e.g. only a preview snippet is available), base your analysis on what is available and note this in your summary.

EMBEDDED LINKS ANALYSIS:
The following links were extracted from the email. Each entry shows the visible display text and the actual domain the link points to. Pay close attention to mismatches — this is a primary phishing technique.
${email.links.length > 0 ?
  email.links.map(l => `  - Display: "${l.display}" → Actual domain: ${l.href}${l.mismatch ? ' ⚠️ DOMAIN MISMATCH' : ''}`).join('\n')
  : '  (No links found or email not fully loaded)'}

When analyzing links:
1. Flag any link where display text shows one domain but href points to a different domain
2. Flag suspicious TLDs or domains that impersonate known brands (e.g. microsoft-support.net, paypa1.com)
3. Flag URL shorteners (bit.ly, tinyurl, t.co etc) as they hide the real destination
4. Flag redirects through unexpected third-party domains

Respond with this exact JSON structure:
{
  "verdict": "SAFE" | "SUSPICIOUS" | "SPAM" | "PHISHING",
  "phishing_score": <number 0-100>,
  "spam_score": <number 0-100>,
  "reasons": [<string>, <string>, ...],
  "suggested_action": "<string>",
  "summary": "<1-2 sentence summary of findings>"
}`;

  // Send to background worker - result comes back via ANALYSIS_DONE message
  chrome.runtime.sendMessage({ type: 'ANALYZE_EMAIL', prompt });

  // Set a timeout in case something goes wrong
  const timeoutId = setTimeout(() => {
    showError('Timed out. Check the service worker console at chrome://extensions.');
  }, 20000);

  // Store timeout so listener can clear it
  window._oe_timeout = timeoutId;
  window._oe_email = email;
}

// ─── UI States ───────────────────────────────────────────────────────────────

function setLoading() {
  document.getElementById('oe-body').innerHTML = `
    <div id="oe-loading">
      <div class="oe-spinner"></div>
      <p>Analyzing email...</p>
    </div>
  `;
  document.getElementById('oe-analyze-btn').style.display = 'none';
}

function showError(msg) {
  document.getElementById('oe-body').innerHTML = `
    <div class="oe-error">
      <span>⚠️</span>
      <p>${msg}</p>
    </div>
  `;
  document.getElementById('oe-analyze-btn').style.display = 'block';
}

function showResult(result, email) {
  const verdictClass = {
    'SAFE': 'verdict-safe',
    'SUSPICIOUS': 'verdict-suspicious',
    'SPAM': 'verdict-spam',
    'PHISHING': 'verdict-phishing'
  }[result.verdict] || 'verdict-suspicious';

  const verdictIcon = {
    'SAFE': '✅',
    'SUSPICIOUS': '⚠️',
    'SPAM': '🚫',
    'PHISHING': '🎣'
  }[result.verdict] || '⚠️';

  const reasonsHTML = (result.reasons || [])
    .map(r => `<li>${r}</li>`)
    .join('');

  document.getElementById('oe-body').innerHTML = `
    <div class="oe-result">
      <div class="oe-verdict ${verdictClass}">
        <span class="oe-verdict-icon">${verdictIcon}</span>
        <span class="oe-verdict-label">${result.verdict}</span>
      </div>

      <div class="oe-scores">
        <div class="oe-score">
          <label>Phishing Risk</label>
          <div class="oe-bar-wrap">
            <div class="oe-bar phishing-bar" style="width:${result.phishing_score}%"></div>
          </div>
          <span>${result.phishing_score}/100</span>
        </div>
        <div class="oe-score">
          <label>Spam Score</label>
          <div class="oe-bar-wrap">
            <div class="oe-bar spam-bar" style="width:${result.spam_score}%"></div>
          </div>
          <span>${result.spam_score}/100</span>
        </div>
      </div>

      <div class="oe-section">
        <h4>Summary</h4>
        <p>${result.summary}</p>
      </div>

      ${reasonsHTML ? `
      <div class="oe-section">
        <h4>Why it's suspicious</h4>
        <ul>${reasonsHTML}</ul>
      </div>` : ''}

      ${email.links && email.links.length > 0 ? `
      <div class="oe-section ${email.links.some(l => l.mismatch) ? 'oe-links-danger' : ''}">
        <h4>🔗 Links (${email.links.length})</h4>
        ${email.links.map(l => `
          <div class="oe-link-row ${l.mismatch ? 'oe-link-mismatch' : ''}">
            <div class="oe-link-display">${l.display}</div>
            <div class="oe-link-href">→ ${l.href}${l.mismatch ? ' ⚠️' : ''}</div>
          </div>
        `).join('')}
      </div>` : ''}

      <div class="oe-section oe-action">
        <h4>Suggested Action</h4>
        <p>${result.suggested_action}</p>
      </div>
    </div>
  `;

  const btn = document.getElementById('oe-analyze-btn');
  btn.style.display = 'block';
  btn.textContent = '🔄 Analyze Another';
  btn.disabled = false;
}

function showEmailReady(subject) {
  document.getElementById('oe-body').innerHTML = `
    <div id="oe-idle">
      <p class="oe-email-subject">📨 ${subject.slice(0, 60)}${subject.length > 60 ? '…' : ''}</p>
      <p class="oe-hint">Click Analyze to check this email for threats.</p>
    </div>
  `;
  document.getElementById('oe-analyze-btn').style.display = 'block';
  document.getElementById('oe-analyze-btn').textContent = '🔍 Analyze Email';
}

// ─── Email Change Detection ───────────────────────────────────────────────────

function getSelectedEmailId() {
  // Use the selected row's aria-label or data attribute as a stable ID
  const selectedRow = document.querySelector('[aria-selected="true"]');
  if (selectedRow) {
    // Try aria-label first as it's most stable
    const label = selectedRow.getAttribute('aria-label');
    if (label && label.length > 2) return label;
    // Try data-convid or similar unique attributes
    const convId = selectedRow.getAttribute('data-convid') ||
                   selectedRow.getAttribute('data-itemid') ||
                   selectedRow.getAttribute('id');
    if (convId) return convId;
    // Fall back to subject text - but only from specific subject elements, not any span
    const subjectEl = selectedRow.querySelector('[class*="subject" i]') ||
                      selectedRow.querySelector('[class*="Subject"]');
    if (subjectEl?.innerText?.trim()) return subjectEl.innerText.trim();
  }
  // Fall back to open email heading
  const headings = document.querySelectorAll('h1, [data-testid="subject"], [aria-label="Message subject"]');
  for (const el of headings) {
    const text = el.innerText?.trim();
    if (text && text.length > 1 && text.length < 300) return text;
  }
  return null;
}

function checkForEmailChange() {
  // Use the From button aria-label as stable email ID since it contains sender email
  const pane = getReadingPane();
  const fromBtn = pane.querySelector('button[aria-label*="From:"]') ||
                  pane.querySelector('[aria-label*="From:"]');
  
  // Also try selected row for subject
  const selectedRow = document.querySelector('[aria-selected="true"]');
  const selectedLabel = selectedRow?.getAttribute('aria-label') || '';
  
  const emailId = (fromBtn?.getAttribute('aria-label') || '') + selectedLabel;

  if (emailId && emailId.length > 5 && emailId !== lastEmailId) {
    lastEmailId = emailId;
    const displaySubject = findTextIn(pane, [
      '[data-testid="subject"]',
      '[aria-label="Message subject"]',
      'h1',
      '[role="heading"]',
    ]) || selectedLabel.slice(0, 80);
    showEmailReady(displaySubject || 'Email selected');
    // Reveal real link destinations automatically
    setTimeout(revealLinks, 500);
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────

function init() {
  createSidebar();

  // Poll every second for selection/email changes
  setInterval(checkForEmailChange, 1000);

  // MutationObserver for faster response
  observer = new MutationObserver(() => {
    checkForEmailChange();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['aria-selected']
  });

  setTimeout(checkForEmailChange, 2000);
}

// Listen for analysis results from background worker
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'ANALYSIS_DONE') {
    clearTimeout(window._oe_timeout);
    if (message.error) {
      showError('Analysis failed: ' + message.error);
      return;
    }
    if (!message.result) {
      showError('No result received. Please try again.');
      return;
    }
    showResult(message.result, window._oe_email || {});
  }
});

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  setTimeout(init, 1500);
}
