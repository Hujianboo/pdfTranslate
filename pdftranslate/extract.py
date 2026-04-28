from pathlib import Path

import pypdfium2 as pdfium

from pdftranslate.markdown import ExtractedPage


def _extract_page_text(page: pdfium.PdfPage) -> str:
    textpage = page.get_textpage()
    try:
        return textpage.get_text_range()
    finally:
        textpage.close()


def extract_pdf_text(pdf_path: str | Path) -> list[ExtractedPage]:
    document = pdfium.PdfDocument(str(pdf_path))
    try:
        pages: list[ExtractedPage] = []
        for index in range(len(document)):
            page = document[index]
            try:
                text = _extract_page_text(page)
            finally:
                page.close()
            pages.append(ExtractedPage(page_number=index + 1, text=text))
        return pages
    finally:
        document.close()
