# Clarivise Documentation

Complete guides and manuals for Clarivise Scan and Shield products.

## Documents

### scan-quickstart.md
**Clarivise Scan — Quick Start Guide**
- Installation for Chrome and Edge
- Configuration (proxy URL, extension token)
- How to analyze emails
- Troubleshooting and best practices
- Data privacy

### shield-hosted.md
**Clarivise Shield — Hosted Deployment**
- Overview of hosted Shield
- Prerequisites and configuration
- Mail flow rule setup in Microsoft 365
- Admin dashboard overview
- Monitoring and troubleshooting
- FAQ section

### shield-azure.md
**Clarivise Shield — Self-Hosted (Azure) Deployment**
- Architecture overview
- Step-by-step Azure setup (Container Registry, Key Vault, Container Apps)
- Docker image build and push
- Mail flow rule configuration
- Monitoring and maintenance
- Scaling and cost estimation
- Troubleshooting

### faq.md
**Frequently Asked Questions**
- General questions
- Clarivise Scan FAQs
- Clarivise Shield FAQs
- Data & privacy
- Technical questions
- Billing & support

## PDF Generation

### Requirements
```bash
pip install -r docs-requirements.txt
# Also install wkhtmltopdf: https://wkhtmltopdf.org/
```

### Usage

Generate all PDFs:
```bash
python ../portal/generate_docs.py
```

Generate a single PDF:
```bash
python ../portal/generate_docs.py --document scan
python ../portal/generate_docs.py --document shield-hosted
python ../portal/generate_docs.py --document shield-azure
python ../portal/generate_docs.py --document faq
```

### Output

PDFs are saved to `docs/pdf/` directory:
- `Clarivise_Scan_QuickStart.pdf`
- `Clarivise_Shield_Hosted.pdf`
- `Clarivise_Shield_SelfHosted_Azure.pdf`
- `Clarivise_FAQ.pdf`

## Updating Documentation

1. Edit the `.md` file directly
2. Run the PDF generator to create updated PDFs
3. Commit both `.md` and `.pdf` files to git

## Portal Integration

Users can download PDFs from the **Download Guides** page in the Clarivise portal:
- Path: `/portal/pages/4_Download_Guides.py`
- Appears after signup or key generation
- Shows all available guides with download buttons

## Branding

Each document includes:
- Clarivise branding (logo, color scheme)
- Generated date
- Version number
- Copyright notice
- Professional formatting with tables, code blocks, lists

Color scheme:
- **Scan:** Indigo (`#4f46e5`)
- **Shield:** Blue (`#2E75B6`)
- **FAQ/General:** Slate (`#0f172a`)

## Standards

- **Format:** Markdown (CommonMark)
- **PDF styling:** Professional, clean, print-friendly
- **Audience:** Non-technical to intermediate (IT admins, end users)
- **Length:** 4,000–12,000 words per document
- **Updates:** Quarterly or as features change

---

**Last Updated:** May 2026  
**Maintained by:** Ingot Solutions (Clarivise Team)
