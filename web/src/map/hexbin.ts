// Deliberately approximate hexagonal binning for the "come le mappe
// cambiano le percezioni" demonstration (see App.tsx, section 5). This is
// an illustrative aid about how spatial aggregation affects perception,
// not a rigorous equal-area spatial analysis — a light longitude
// correction (cos(latitude)) keeps hexagons roughly regular on screen
// over Trentino's small extent, but no attempt is made at a true
// equal-area projection. See AGENTS.md: never imply more precision than
// a method actually has.
//
// Flat-topped axial hex grid, formulas per the standard reference
// (redblobgames.com/grids/hexagons).
export interface HexBin {
  // Geometric center of the hex cell — used to draw the cell's polygon.
  // Deliberately NOT used to place a point symbol: it's a property of
  // the grid, not of the data, and can fall in a spot with no nearby
  // observations (e.g. a cell whose points all sit near one edge). Point
  // symbols (cluster-fixed / cluster-proportional) use `centroid`
  // instead, the mean position of the actual points in the cell.
  center: [number, number];
  centroid: [number, number];
  count: number;
  polygon: [number, number][];
}

const SQRT3 = Math.sqrt(3);

function axialRound(qf: number, rf: number): { q: number; r: number } {
  const x = qf;
  const z = rf;
  const y = -x - z;

  let rx = Math.round(x);
  let ry = Math.round(y);
  let rz = Math.round(z);

  const xDiff = Math.abs(rx - x);
  const yDiff = Math.abs(ry - y);
  const zDiff = Math.abs(rz - z);

  if (xDiff > yDiff && xDiff > zDiff) {
    rx = -ry - rz;
  } else if (yDiff > zDiff) {
    ry = -rx - rz;
  } else {
    rz = -rx - ry;
  }

  return { q: rx, r: rz };
}

export function binPointsIntoHexagons(
  points: [number, number][],
  cellSizeDegrees: number,
  referenceLatitude: number
): HexBin[] {
  const lonScale = Math.cos((referenceLatitude * Math.PI) / 180) || 1;

  const counts = new Map<
    string,
    { q: number; r: number; count: number; lonSum: number; latSum: number }
  >();
  for (const [lon, lat] of points) {
    const x = lon * lonScale;
    const y = lat;
    const qf = (2 / 3) * (x / cellSizeDegrees);
    const rf = (-1 / 3) * (x / cellSizeDegrees) + (SQRT3 / 3) * (y / cellSizeDegrees);
    const { q, r } = axialRound(qf, rf);
    const key = `${q},${r}`;
    const existing = counts.get(key);
    if (existing) {
      existing.count += 1;
      existing.lonSum += lon;
      existing.latSum += lat;
    } else {
      counts.set(key, { q, r, count: 1, lonSum: lon, latSum: lat });
    }
  }

  return [...counts.values()].map(({ q, r, count, lonSum, latSum }) => {
    const cx = (cellSizeDegrees * ((3 / 2) * q)) / lonScale;
    const cy = cellSizeDegrees * (SQRT3 * (r + q / 2));
    const polygon: [number, number][] = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 180) * (60 * i);
      polygon.push([
        cx + (cellSizeDegrees * Math.cos(angle)) / lonScale,
        cy + cellSizeDegrees * Math.sin(angle),
      ]);
    }
    polygon.push(polygon[0]);
    const centroid: [number, number] = [lonSum / count, latSum / count];
    return { center: [cx, cy] as [number, number], centroid, count, polygon };
  });
}
