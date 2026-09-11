"""Regression fixtures for caption/continuation ordering on rendered pages."""
import sys
import tempfile
import unittest
from pathlib import Path
import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_pdf import check
from a14_latex import convert


class PdfLayoutTests(unittest.TestCase):
    def inspect_blocks(self, blocks):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.pdf"
            doc = fitz.open()
            page = doc.new_page()
            for i, text in enumerate(blocks):
                page.insert_text((55, 55 + 35 * i), text)
            doc.save(path)
            doc.close()
            return check(path)[1]

    def test_continuation_before_caption_is_rejected(self):
        self.assertTrue(self.inspect_blocks([
            "Running head", "(table continued)", "Column A   Column B",
            "Table 7. Material uncertainties", "Column A   Column B", "Data 1   Data 2"]))

    def test_continuation_before_heading_is_rejected(self):
        self.assertTrue(self.inspect_blocks([
            "Running head", "(table continued)", "Column A   Column B", "4. Results"]))

    def test_genuine_continuation_with_rows_is_allowed(self):
        self.assertFalse(self.inspect_blocks([
            "Running head", "(table continued)", "Column A   Column B", "Data 1   Data 2"]))

    def test_caption_and_table_are_measured_together(self):
        md = "**Table 7. Example.** Description.\n\n| A | B |\n|---|---|\n| x | y |\n"
        tex = convert(md, {"measured_tables": True})
        self.assertIn(r"\begin{lrbox}", tex)
        self.assertIn(r"\Needspace{\dimexpr\ht\reporttablebox", tex)
        self.assertNotIn(r"\begin{longtable}", tex)
        self.assertEqual(tex.count("Table 7."), 1)

    def test_adjacent_headings_share_one_reservation(self):
        tex=convert("## 2. Evidence\n\n### Meteorology\n\nSupporting evidence.\n",{"flow_barriers":True})
        self.assertIn(r"\needspace{10\baselineskip}",tex)
        between=tex.split(r"\section{2. Evidence}")[1].split(r"\subsection{Meteorology}")[0]
        self.assertNotIn(r"\FloatBarrier",between)
        self.assertNotIn(r"\needspace",between)

    def test_reference_list_preserves_start_number(self):
        tex=convert("9. First added source.\n10. Second added source.\n",{})
        self.assertIn("start=9",tex)

    def test_last_body_heading_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"orphan.pdf"
            doc=fitz.open();page=doc.new_page()
            page.insert_text((55,100),"A preceding paragraph.")
            page.insert_text((55,550),"2. Evidence and data quality",fontsize=12,fontname="hebo")
            page.insert_text((280,810),"3",fontsize=9)
            doc.save(path);doc.close()
            self.assertTrue(check(path)[1])

    def test_period_terminated_appendix_heading_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"appendix-orphan.pdf"
            doc=fitz.open();page=doc.new_page()
            page.insert_text((55,100),"Preceding reference.")
            page.insert_text((55,500),"Appendix. Definitions",fontsize=11,fontname="hebo")
            page.insert_text((280,810),"42",fontsize=9)
            doc.save(path);doc.close()
            self.assertTrue(check(path)[1])

    def test_contents_appendix_entry_is_not_orphan_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"contents.pdf"
            doc=fitz.open();page=doc.new_page()
            page.insert_text((55,500),"Appendix C - Limitations",fontsize=11,fontname="hebo")
            page.insert_text((520,500),"158",fontsize=11,fontname="hebo")
            page.insert_text((280,810),"7",fontsize=9)
            doc.save(path);doc.close()
            self.assertFalse(check(path)[1])


if __name__ == "__main__":
    unittest.main()
