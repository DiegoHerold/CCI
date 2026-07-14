import type { ExcelCellPreview, ExcelSheetPreview } from "../types/preview";

export function cellKey(row: number, column: number) {
  return `${row}:${column}`;
}

export function buildCellMap(sheet: ExcelSheetPreview) {
  const map = new Map<string, ExcelCellPreview>();
  for (const cell of sheet.cells) map.set(cellKey(cell.row, cell.column), cell);
  return map;
}

export function columnLetter(column: number) {
  let value = column;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

export function cellAddress(row: number, column: number) {
  return `${columnLetter(column)}${row}`;
}

export function parseRange(range: string) {
  const [start, end = start] = range.split(":");
  const parse = (address: string) => {
    const match = /^([A-Z]+)(\d+)$/i.exec(address.trim());
    if (!match) return null;
    const [, letters, row] = match;
    let column = 0;
    for (const char of letters.toUpperCase()) {
      column = column * 26 + (char.charCodeAt(0) - 64);
    }
    return { row: Number(row), column };
  };
  const startCell = parse(start);
  const endCell = parse(end);
  if (!startCell || !endCell) return null;
  return {
    start_row: Math.min(startCell.row, endCell.row),
    end_row: Math.max(startCell.row, endCell.row),
    start_column: Math.min(startCell.column, endCell.column),
    end_column: Math.max(startCell.column, endCell.column),
  };
}

export function isCellInRange(row: number, column: number, range?: ReturnType<typeof parseRange>) {
  if (!range) return false;
  return row >= range.start_row && row <= range.end_row && column >= range.start_column && column <= range.end_column;
}
