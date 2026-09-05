"""P6 — PDF renderer for the branded score report.

Tries backends in order:
    1. WeasyPrint (best fidelity — full HTML/CSS)
    2. ReportLab (basic layout — installed in most environments)
    3. Minimal plaintext PDF (self-contained, no deps — guarantees the
       endpoint always returns a valid `application/pdf` body).

The endpoint contract is: byte-string PDF, `Content-Type: application/pdf`.
Backend selection is transparent to the caller.
"""

from __future__ import annotations

import html
import io
import re
import zlib


def _extract_text(html_str: str) -> list[str]:
    """Strip HTML tags → line-broken plain text (footer-safe)."""
    # Convert block-ish tags to newlines first.
    s = re.sub(r"</(?:p|h1|h2|h3|li|tr|div|footer|header)>", "\n", html_str, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    lines = [ln.strip() for ln in s.splitlines()]
    return [ln for ln in lines if ln]


def _minimal_pdf(text_lines: list[str]) -> bytes:
    """Emit a valid single/multi-page PDF containing the given text.

    Uses a hand-rolled writer so we can guarantee this works offline with no
    external dependency. Enough for CI/pilot; production installs WeasyPrint.
    """
    # Page geometry
    page_w, page_h = 612, 792   # US Letter, points
    left, top = 54, 750
    line_h = 14
    max_chars = 90

    # Wrap long lines
    wrapped: list[str] = []
    for ln in text_lines:
        if not ln:
            wrapped.append("")
            continue
        while len(ln) > max_chars:
            cut = ln.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            wrapped.append(ln[:cut])
            ln = ln[cut:].lstrip()
        wrapped.append(ln)

    lines_per_page = max(1, (top - 60) // line_h)
    pages = [wrapped[i:i + lines_per_page] for i in range(0, len(wrapped), lines_per_page)] or [[""]]

    def _escape_pdf_str(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    objects: list[bytes] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    # 1: Catalog (points to 2)
    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages (patched with kids ids later)
    pages_id = add_object(b"")  # placeholder
    # Font resource dictionary
    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for page_lines in pages:
        # Build content stream
        content_lines = [b"BT", b"/F1 11 Tf", f"{left} {top} Td".encode()]
        first = True
        for ln in page_lines:
            if first:
                content_lines.append(f"({_escape_pdf_str(ln)}) Tj".encode())
                first = False
            else:
                content_lines.append(f"0 -{line_h} Td".encode())
                content_lines.append(f"({_escape_pdf_str(ln)}) Tj".encode())
        content_lines.append(b"ET")
        stream_body = b"\n".join(content_lines)
        compressed = zlib.compress(stream_body)
        content_obj = (
            b"<< /Length " + str(len(compressed)).encode() + b" /Filter /FlateDecode >>\n"
            b"stream\n" + compressed + b"\nendstream"
        )
        content_id = add_object(content_obj)

        page_obj = (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 " + f"{page_w} {page_h}".encode() + b"] "
            b"/Resources << /Font << /F1 " + str(font_id).encode() + b" 0 R >> >> "
            b"/Contents " + str(content_id).encode() + b" 0 R >>"
        )
        page_ids.append(add_object(page_obj))

    kids = b" ".join(f"{pid} 0 R".encode() for pid in page_ids)
    objects[pages_id - 1] = (
        b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode() + b" >>"
    )

    # Serialize
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode())
        out.write(obj)
        out.write(b"\nendobj\n")
    xref_off = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(b"trailer\n")
    out.write(f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n".encode())
    out.write(b"startxref\n" + str(xref_off).encode() + b"\n%%EOF")
    return out.getvalue()


def html_to_pdf(html_str: str) -> tuple[bytes, str]:
    """Return (pdf_bytes, backend_name)."""
    # 1. WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore
        return HTML(string=html_str).write_pdf(), "weasyprint"
    except Exception:
        pass
    # 2. ReportLab (very basic — a text render)
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        from reportlab.lib.pagesizes import letter  # type: ignore

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        y = 750
        for ln in _extract_text(html_str):
            if y < 60:
                c.showPage()
                y = 750
            c.drawString(54, y, ln[:100])
            y -= 14
        c.save()
        return buf.getvalue(), "reportlab"
    except Exception:
        pass
    # 3. Minimal built-in fallback
    return _minimal_pdf(_extract_text(html_str)), "builtin-minimal"


__all__ = ["html_to_pdf"]
