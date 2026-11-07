"""
Pure-Python Zero-Dependency PDF Certificate Builder.
Generates an official, publication-quality A4 Plan Certificate PDF
with ordinance citations, verification seal, and rule audit table.
"""

import io
from typing import Dict, Any
from backend.rules.certificate import PlanCertificate

class PurePDFBuilder:
    """
    Constructs a standard, well-formed PDF 1.4 document from scratch
    without external dependencies (e.g. ReportLab or Weasyprint).
    """

    def __init__(self):
        self.stream = io.BytesIO()
        self.objects = []
        self.page_width = 595.28   # A4 portrait width in points
        self.page_height = 841.89  # A4 portrait height in points

    def _escape_pdf_text(self, text: str) -> str:
        """Escapes parentheses and backslashes for PDF string literals."""
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def build_certificate_pdf(self, cert: PlanCertificate, student_profile: Dict[str, Any]) -> bytes:
        """
        Builds a crisp, single-page A4 Academic Plan Verification Certificate.
        """
        content_ops = []

        # Color helpers (PDF 0.0 - 1.0 RGB)
        # Background: subtle off-white #FAF9F7 (0.98, 0.976, 0.969)
        content_ops.append("0.980 0.976 0.969 rg")
        content_ops.append(f"0 0 {self.page_width:.2f} {self.page_height:.2f} re f")

        # Header card background: pure white
        content_ops.append("1.0 1.0 1.0 rg")
        content_ops.append(f"28 28 {self.page_width - 56:.2f} {self.page_height - 56:.2f} re f")

        # Outer border: #E6E2DA (0.90, 0.88, 0.85)
        content_ops.append("0.902 0.886 0.855 RG")
        content_ops.append("1 w")
        content_ops.append(f"28 28 {self.page_width - 56:.2f} {self.page_height - 56:.2f} re S")

        # Top Accent Header Bar
        # Accent red: #C8341E (0.784, 0.204, 0.118)
        content_ops.append("0.784 0.204 0.118 rg")
        content_ops.append(f"28 {self.page_height - 34:.2f} {self.page_width - 56:.2f} 6 re f")

        # Header Titles
        # Title: "INDIAN INSTITUTE OF TECHNOLOGY BHILAI"
        content_ops.append("0.333 0.322 0.294 rg") # ink-2
        content_ops.append("BT /F1 9 Tf 44 790 Td (INDIAN INSTITUTE OF TECHNOLOGY BHILAI - ACADEMIC ADVISING) Tj ET")

        content_ops.append("0.106 0.102 0.090 rg") # ink
        content_ops.append("BT /F2 18 Tf 44 766 Td (Academic Plan Verification Certificate) Tj ET")

        # Validity Badge
        status_text = "VERIFIED ACCREDITED" if cert.is_valid else "VERIFICATION FAILED"
        badge_bg = "0.184 0.490 0.310" if cert.is_valid else "0.706 0.137 0.094" # success green or danger red
        content_ops.append(f"{badge_bg} rg")
        content_ops.append("430 760 120 20 re f")
        content_ops.append("1.0 1.0 1.0 rg")
        content_ops.append(f"BT /F2 9 Tf 442 766 Td ({status_text}) Tj ET")

        # Metadata Grid (horizontal rule at 748)
        content_ops.append("0.902 0.886 0.855 RG")
        content_ops.append(f"44 748 m {self.page_width - 44:.2f} 748 l S")

        student_name = self._escape_pdf_text(student_profile.get("name", "Bhilai Student"))
        stu_id = self._escape_pdf_text(cert.student_id)
        prog = self._escape_pdf_text(student_profile.get("programme", "BH-CSE-BTECH (B.Tech CSE)"))
        cgpa = f"{float(student_profile.get('cgpa', 8.50)):.2f}"
        gen_date = self._escape_pdf_text(cert.generated_at[:19].replace('T', ' ') + " UTC")

        content_ops.append("0.333 0.322 0.294 rg")
        content_ops.append("BT /F1 8 Tf 44 734 Td (STUDENT NAME) Tj ET")
        content_ops.append("BT /F1 8 Tf 180 734 Td (STUDENT ID) Tj ET")
        content_ops.append("BT /F1 8 Tf 270 734 Td (PROGRAMME) Tj ET")
        content_ops.append("BT /F1 8 Tf 370 734 Td (CGPA) Tj ET")
        content_ops.append("BT /F1 8 Tf 430 734 Td (ISSUED TIMESTAMP) Tj ET")

        content_ops.append("0.106 0.102 0.090 rg")
        content_ops.append(f"BT /F2 9 Tf 44 720 Td ({student_name}) Tj ET")
        content_ops.append(f"BT /F2 9 Tf 180 720 Td ({stu_id}) Tj ET")
        content_ops.append(f"BT /F2 9 Tf 270 720 Td ({prog}) Tj ET")
        content_ops.append(f"BT /F2 9 Tf 370 720 Td ({cgpa}) Tj ET")
        content_ops.append(f"BT /F2 8 Tf 430 720 Td ({gen_date}) Tj ET")

        content_ops.append("0.902 0.886 0.855 RG")
        content_ops.append(f"44 710 m {self.page_width - 44:.2f} 710 l S")

        # Cryptographic Seal Banner
        content_ops.append("0.953 0.945 0.929 rg") # surface-2
        content_ops.append(f"44 670 {self.page_width - 88:.2f} 32 re f")
        content_ops.append("0.902 0.886 0.855 RG")
        content_ops.append(f"44 670 {self.page_width - 88:.2f} 32 re S")

        cert_hash = cert.certificate_hash or cert.compute_hash()
        content_ops.append("0.333 0.322 0.294 rg")
        content_ops.append("BT /F1 7.5 Tf 52 690 Td (SHA-256 CANONICAL SEAL:) Tj ET")
        content_ops.append("0.106 0.102 0.090 rg")
        content_ops.append(f"BT /F2 8 Tf 175 690 Td ({cert_hash[:48]}...) Tj ET")
        content_ops.append("0.333 0.322 0.294 rg")
        content_ops.append(f"BT /F1 7 Tf 52 678 Td (KB VERSION: {cert.kb_version}  |  RULESET: {cert.rule_set_version}  |  INPUT HASH: {cert.input_hash}) Tj ET")

        # Rules Evaluation Table
        content_ops.append("0.106 0.102 0.090 rg")
        content_ops.append("BT /F2 11 Tf 44 646 Td (Audited Ordinance Clauses & Statutory Rule Results) Tj ET")

        # Table Header
        table_top = 636
        content_ops.append("0.953 0.945 0.929 rg")
        content_ops.append(f"44 {table_top - 18} {self.page_width - 88:.2f} 18 re f")
        content_ops.append("0.333 0.322 0.294 rg")
        content_ops.append(f"BT /F2 8 Tf 50 {table_top - 12} Td (CLAUSE) Tj ET")
        content_ops.append(f"BT /F2 8 Tf 110 {table_top - 12} Td (RULE TITLE / REQUIREMENT) Tj ET")
        content_ops.append(f"BT /F2 8 Tf 350 {table_top - 12} Td (STATUS) Tj ET")
        content_ops.append(f"BT /F2 8 Tf 410 {table_top - 12} Td (OBSERVED VALUE / MARGIN) Tj ET")

        # Table Rows
        curr_y = table_top - 18
        row_height = 20

        # Take first 14 representative results for clean 1-page fit
        display_results = cert.results[:15]
        for idx, res in enumerate(display_results):
            curr_y -= row_height
            # Row hairline
            content_ops.append("0.94 0.93 0.91 RG")
            content_ops.append(f"44 {curr_y} m {self.page_width - 44:.2f} {curr_y} l S")

            # Alternate background fill
            if idx % 2 == 1:
                content_ops.append("0.985 0.982 0.978 rg")
                content_ops.append(f"44 {curr_y} {self.page_width - 88:.2f} {row_height} re f")

            # Clause ID
            clause = self._escape_pdf_text(res.clause_id or "ORD-SPEC")
            content_ops.append("0.169 0.361 0.541 rg") # info blue
            content_ops.append(f"BT /F2 7.5 Tf 50 {curr_y + 6} Td ({clause}) Tj ET")

            # Rule Title
            title = self._escape_pdf_text(res.rule_title[:45])
            content_ops.append("0.106 0.102 0.090 rg")
            content_ops.append(f"BT /F1 8 Tf 110 {curr_y + 6} Td ({title}) Tj ET")

            # Status pill
            is_pass = (res.status.value == "pass")
            is_warn = (res.status.value == "warn")
            status_color = "0.184 0.490 0.310" if is_pass else ("0.718 0.475 0.122" if is_warn else "0.706 0.137 0.094")
            content_ops.append(f"{status_color} rg")
            content_ops.append(f"BT /F2 7.5 Tf 350 {curr_y + 6} Td ({res.status.value.upper()}) Tj ET")

            # Observed & Margin
            margin_str = f" [margin: {res.margin:+.1f}]" if res.margin is not None else ""
            obs_clean = self._escape_pdf_text(str(res.observed)[:22] + margin_str)
            content_ops.append("0.333 0.322 0.294 rg")
            content_ops.append(f"BT /F1 7.5 Tf 410 {curr_y + 6} Td ({obs_clean}) Tj ET")

        # Bottom Summary Card
        summary_y = 65
        content_ops.append("0.953 0.945 0.929 rg")
        content_ops.append(f"44 {summary_y} {self.page_width - 88:.2f} 42 re f")
        content_ops.append("0.902 0.886 0.855 RG")
        content_ops.append(f"44 {summary_y} {self.page_width - 88:.2f} 42 re S")

        t_margin = cert.summary.tightest_margin
        tightest_text = f"Tightest Constraint Margin: {t_margin.margin:+.1f} on {t_margin.rule_title} ({t_margin.scope_ref})" if t_margin else "All constraints satisfied with ample margin."
        tightest_escaped = self._escape_pdf_text(tightest_text)

        content_ops.append("0.106 0.102 0.090 rg")
        content_ops.append(f"BT /F2 8.5 Tf 52 {summary_y + 26} Td (Audit Summary: {cert.summary.passed}/{cert.summary.total_rules} rules satisfied  |  {cert.summary.warned} advisory warnings  |  {cert.summary.failed} statutory violations) Tj ET")
        content_ops.append("0.333 0.322 0.294 rg")
        content_ops.append(f"BT /F1 8 Tf 52 {summary_y + 12} Td ({tightest_escaped}) Tj ET")

        # Footer
        content_ops.append("0.541 0.525 0.486 rg")
        content_ops.append(f"BT /F1 7 Tf 44 42 Td (Official Machine-Verifiable Document  *  Verify online: https://academic-advisor.local/verify?hash={cert_hash[:16]}) Tj ET")
        content_ops.append(f"BT /F1 7 Tf {self.page_width - 150:.2f} 42 Td (Page 1 of 1  *  Deterministic Seal) Tj ET")

        # Assemble PDF stream
        stream_content = "\n".join(content_ops).encode("latin1", errors="replace")
        stream_len = len(stream_content)

        # PDF Object structure:
        # 1 0: Catalog
        # 2 0: Pages
        # 3 0: Page
        # 4 0: Contents stream
        # 5 0: Font F1 (Helvetica)
        # 6 0: Font F2 (Helvetica-Bold)

        obj_offsets = []
        out = io.BytesIO()
        out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        # Obj 1: Catalog
        obj_offsets.append(out.tell())
        out.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        # Obj 2: Pages
        obj_offsets.append(out.tell())
        out.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

        # Obj 3: Page
        obj_offsets.append(out.tell())
        page_dict = (
            f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width:.2f} {self.page_height:.2f}] "
            f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj\n"
        ).encode("ascii")
        out.write(page_dict)

        # Obj 4: Content Stream
        obj_offsets.append(out.tell())
        out.write(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("ascii"))
        out.write(stream_content)
        out.write(b"\nendstream\nendobj\n")

        # Obj 5: Font F1 (Helvetica)
        obj_offsets.append(out.tell())
        out.write(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

        # Obj 6: Font F2 (Helvetica-Bold)
        obj_offsets.append(out.tell())
        out.write(b"6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")

        # XRef table
        xref_offset = out.tell()
        num_objects = len(obj_offsets) + 1
        out.write(f"xref\n0 {num_objects}\n0000000000 65535 f \n".encode("ascii"))
        for off in obj_offsets:
            out.write(f"{off:010d} 00000 n \n".encode("ascii"))

        # Trailer
        out.write(
            f"trailer\n<< /Size {num_objects} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )

        return out.getvalue()

pdf_builder = PurePDFBuilder()

