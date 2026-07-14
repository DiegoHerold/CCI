import type { BoundingBox } from "../types/preview";

export function scalePdfBox(bbox: BoundingBox, scale: number) {
  return {
    left: bbox.x0 * scale,
    top: bbox.y0 * scale,
    width: Math.max(1, (bbox.x1 - bbox.x0) * scale),
    height: Math.max(1, (bbox.y1 - bbox.y0) * scale),
  };
}

export function normalizePdfBox(start: { x: number; y: number }, end: { x: number; y: number }): BoundingBox {
  return {
    x0: Math.min(start.x, end.x),
    y0: Math.min(start.y, end.y),
    x1: Math.max(start.x, end.x),
    y1: Math.max(start.y, end.y),
  };
}

export function isSameBox(a?: BoundingBox, b?: BoundingBox) {
  if (!a || !b) return false;
  return a.x0 === b.x0 && a.y0 === b.y0 && a.x1 === b.x1 && a.y1 === b.y1;
}
