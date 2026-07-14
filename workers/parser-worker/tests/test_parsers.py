import sys
from io import BytesIO
from pathlib import Path

import fitz
from openpyxl import Workbook

WORKER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKER_ROOT))

from app.parsers import parse_document, parse_pdf, parse_xlsx, serialize_preview


def make_pdf_with_text() -> bytes:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((50, 80), "Conta Descricao Saldo Atual")
    return document.tobytes()


def make_blank_pdf() -> bytes:
    document = fitz.open()
    document.new_page(width=595, height=842)
    return document.tobytes()


def make_xlsx() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Balancete"
    sheet["A1"] = "Conta"
    sheet["B1"] = "Descrição"
    sheet["C1"] = "Saldo Atual"
    sheet["A2"] = "1.1.01"
    sheet["B2"] = "Caixa"
    sheet["C2"] = 1000
    sheet.merge_cells("A4:B4")
    sheet["A4"] = "Observação"
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_pdf_with_text_generates_selectable_blocks() -> None:
    preview = parse_pdf(document_id="doc-1", content=make_pdf_with_text())

    assert preview["file_format"] == "PDF"
    assert preview["requires_ocr"] is False
    assert preview["pages"][0]["text_blocks"]
    assert preview["pages"][0]["text_blocks"][0]["bbox"]["x0"] >= 0


def test_pdf_without_text_marks_requires_ocr() -> None:
    preview = parse_pdf(document_id="doc-1", content=make_blank_pdf())

    assert preview["requires_ocr"] is True
    assert preview["ocr_reason"] == "no_text_layer_detected"


def test_xlsx_preview_preserves_sheets_cells_and_merged_ranges() -> None:
    preview = parse_xlsx(document_id="doc-2", content=make_xlsx())
    sheet = preview["sheets"][0]
    cells_by_address = {cell["address"]: cell for cell in sheet["cells"]}

    assert preview["file_format"] == "XLSX"
    assert sheet["name"] == "Balancete"
    assert cells_by_address["A1"]["value"] == "Conta"
    assert cells_by_address["C2"]["data_type"] == "number"
    assert cells_by_address["A4"]["is_merged"] is True
    assert sheet["merged_cells"][0]["range"] == "A4:B4"
    assert sheet["detected_headers"][0]["row"] == 1
    assert sheet["detected_tables"][0]["range"].startswith("A1:")


def test_dispatch_and_json_size_limit() -> None:
    preview = parse_document(
        document_id="doc-3",
        original_filename="balancete.xlsx",
        file_format="EXCEL",
        content=make_xlsx(),
    )
    raw = serialize_preview(preview, max_size_bytes=100_000)

    assert raw.startswith(b"{")
