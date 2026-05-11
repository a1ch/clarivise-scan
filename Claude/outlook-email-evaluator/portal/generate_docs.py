#!/usr/bin/env python3
"""
Clarivise Documentation PDF Generator

Converts markdown documentation files to professional PDFs with branding.
Requires: pip install markdown2 pdfkit python-markdown-math

Usage:
    python generate_docs.py                    # Generate all PDFs
    python generate_docs.py --document scan    # Generate only Scan quick start
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import markdown2
except ImportError:
    print("Error: markdown2 not installed. Run: pip install markdown2 pdfkit")
    sys.exit(1)


class ClarivisePDFGenerator:
    """Generate Clarivise documentation PDFs from Markdown."""

    # Define documents to generate
    DOCUMENTS = {
        "scan": {
            "title": "Clarivise Scan — Quick Start Guide",
            "source": "docs/scan-quickstart.md",
            "output": "docs/pdf/Clarivise_Scan_QuickStart.pdf",
            "color": "#4f46e5",  # Indigo (Scan branding)
        },
        "shield-hosted": {
            "title": "Clarivise Shield — Hosted Deployment",
            "source": "docs/shield-hosted.md",
            "output": "docs/pdf/Clarivise_Shield_Hosted.pdf",
            "color": "#2E75B6",  # Blue (Shield branding)
        },
        "shield-azure": {
            "title": "Clarivise Shield — Self-Hosted (Azure)",
            "source": "docs/shield-azure.md",
            "output": "docs/pdf/Clarivise_Shield_SelfHosted_Azure.pdf",
            "color": "#2E75B6",  # Blue (Shield branding)
        },
        "faq": {
            "title": "Clarivise — Frequently Asked Questions",
            "source": "docs/faq.md",
            "output": "docs/pdf/Clarivise_FAQ.pdf",
            "color": "#0f172a",  # Slate (neutral)
        },
    }

    def __init__(self, base_path=None):
        """Initialize the generator."""
        self.base_path = Path(base_path or ".")
        self.output_dir = self.base_path / "docs" / "pdf"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def read_markdown(self, doc_key):
        """Read markdown file for a document."""
        source = self.base_path / self.DOCUMENTS[doc_key]["source"]
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        with open(source, "r", encoding="utf-8") as f:
            return f.read()

    def markdown_to_html(self, markdown_text, doc_key):
        """Convert markdown to HTML with Clarivise branding."""
        # Convert markdown to HTML
        html_content = markdown2.markdown(
            markdown_text,
            extras=["tables", "code-friendly", "fenced-code-blocks"],
        )

        # Get branding colors
        color = self.DOCUMENTS[doc_key]["color"]
        title = self.DOCUMENTS[doc_key]["title"]
        generation_date = datetime.now().strftime("%B %d, %Y")

        # Wrap in HTML with CSS styling
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: white;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Cover page */
        .cover {{
            border-bottom: 4px solid {color};
            padding-bottom: 40px;
            margin-bottom: 60px;
            page-break-after: always;
        }}
        
        .cover-brand {{
            font-size: 32px;
            font-weight: 700;
            color: {color};
            margin-bottom: 20px;
            letter-spacing: -0.02em;
        }}
        
        .cover-title {{
            font-size: 28px;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.3;
            margin-bottom: 30px;
        }}
        
        .cover-meta {{
            font-size: 14px;
            color: #64748b;
            margin-bottom: 5px;
        }}

        /* Headers */
        h1 {{
            font-size: 28px;
            font-weight: 700;
            color: {color};
            margin: 40px 0 20px 0;
            page-break-after: avoid;
            letter-spacing: -0.02em;
        }}
        
        h2 {{
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
            margin: 30px 0 15px 0;
            padding-top: 15px;
            page-break-after: avoid;
            border-top: 1px solid #e2e8f0;
        }}
        
        h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #0f172a;
            margin: 20px 0 10px 0;
            page-break-after: avoid;
        }}

        h4 {{
            font-size: 14px;
            font-weight: 600;
            color: #334155;
            margin: 15px 0 8px 0;
        }}

        /* Paragraphs and text */
        p {{
            margin-bottom: 15px;
            line-height: 1.65;
        }}

        /* Lists */
        ul, ol {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}
        
        ul li, ol li {{
            margin-bottom: 8px;
            color: #334155;
        }}
        
        ul li::marker {{
            color: {color};
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
            page-break-inside: avoid;
        }}
        
        thead {{
            background-color: #f1f5f9;
        }}
        
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #0f172a;
            border: 1px solid #e2e8f0;
        }}
        
        td {{
            padding: 10px 12px;
            border: 1px solid #e2e8f0;
            color: #475569;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}

        /* Code blocks */
        pre {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            font-size: 12px;
            line-height: 1.5;
            page-break-inside: avoid;
        }}
        
        code {{
            font-family: 'Courier New', monospace;
        }}
        
        p code {{
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 13px;
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid {color};
            padding-left: 20px;
            margin: 20px 0;
            color: #64748b;
            font-style: italic;
        }}

        /* Horizontal rule */
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 30px 0;
        }}

        /* Strong and emphasis */
        strong {{
            font-weight: 600;
            color: #0f172a;
        }}
        
        em {{
            font-style: italic;
            color: #475569;
        }}

        /* Links */
        a {{
            color: {color};
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}

        /* Page breaks */
        .page-break {{
            page-break-after: always;
        }}

        /* Footer */
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #94a3b8;
            text-align: center;
        }}

        /* Callout boxes */
        .note, .warning, .info {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            page-break-inside: avoid;
        }}
        
        .note {{
            background-color: #eef2ff;
            border-left: 4px solid {color};
            color: #312e81;
        }}
        
        .warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #78350f;
        }}

        /* Responsive spacing */
        @media print {{
            body {{
                padding: 20px;
            }}
            h1, h2 {{
                page-break-after: avoid;
            }}
            table, pre {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <!-- Cover page -->
    <div class="cover">
        <div class="cover-brand">🛡️ Clarivise</div>
        <div class="cover-title">{title}</div>
        <div class="cover-meta">Generated: {generation_date}</div>
        <div class="cover-meta">Version 1.0 — Ingot Solutions</div>
    </div>

    <!-- Content -->
    {html_content}

    <!-- Footer -->
    <div class="footer">
        <p>© 2026 Ingot Solutions. All rights reserved.<br>
        Generated {generation_date} | Clarivise Documentation</p>
    </div>
</body>
</html>
"""
        return html

    def generate_pdf(self, doc_key):
        """Generate PDF for a single document."""
        try:
            print(f"📄 Generating {self.DOCUMENTS[doc_key]['title']}...", end=" ")

            # Read markdown
            markdown_text = self.read_markdown(doc_key)

            # Convert to HTML
            html = self.markdown_to_html(markdown_text, doc_key)

            # Save HTML (for inspection if needed)
            html_path = self.output_dir / f"{doc_key}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            # Output path
            output_path = self.base_path / self.DOCUMENTS[doc_key]["output"]

            # Try to generate PDF using wkhtmltopdf (requires installation)
            try:
                import pdfkit

                options = {
                    "page-size": "A4",
                    "margin-top": "0.5in",
                    "margin-right": "0.5in",
                    "margin-bottom": "0.75in",
                    "margin-left": "0.5in",
                    "encoding": "UTF-8",
                    "no-outline": None,
                    "enable-local-file-access": None,
                }
                pdfkit.from_file(str(html_path), str(output_path), options=options)
                print(f"✅ Done → {output_path}")
            except ImportError:
                print(f"⚠️  (saved HTML, install pdfkit for PDF generation)")
                print(f"   Run: pip install pdfkit")
                print(f"   Then install wkhtmltopdf: https://wkhtmltopdf.org/")

            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def generate_all(self):
        """Generate all PDF documents."""
        print("\n🛡️  Clarivise Documentation PDF Generator\n")
        print(f"Output directory: {self.output_dir}\n")

        results = {}
        for doc_key in self.DOCUMENTS:
            results[doc_key] = self.generate_pdf(doc_key)

        # Summary
        print(f"\n{'='*60}")
        successful = sum(1 for v in results.values() if v)
        print(f"Generated {successful}/{len(results)} PDFs successfully")

        if successful == len(results):
            print("✅ All documentation generated!")
        else:
            print("⚠️  Some PDFs failed. Check the errors above.")

        return all(results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate Clarivise documentation PDFs")
    parser.add_argument(
        "--document",
        choices=["scan", "shield-hosted", "shield-azure", "faq"],
        help="Generate only a specific document",
    )
    parser.add_argument("--base-path", default=".", help="Base path for the repo")

    args = parser.parse_args()

    generator = ClarivisePDFGenerator(args.base_path)

    if args.document:
        generator.generate_pdf(args.document)
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()
