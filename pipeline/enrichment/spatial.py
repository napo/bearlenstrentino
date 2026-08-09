"""Metric-CRS spatial calculations for OSM enrichment (Milestone 8).

Everything reprojects to EPSG:32632 (UTM zone 32N) before measuring
distances/areas in meters — WGS84 lon/lat degrees are not equidistant
and can't be used directly for buffers or distances (see AGENTS.md,
"documentare le assunzioni GIS"). UTM 32N is appropriate for Trentino's
longitude range (~10.5-11.9°E); it would need reconsidering for a much
larger or differently-located study area.
"""
from __future__ import annotations

from dataclasses import dataclass

from pyproj import Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform
from shapely.strtree import STRtree

_WGS84_TO_UTM32N = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True).transform


def to_utm32n(geom: BaseGeometry) -> BaseGeometry:
    return shapely_transform(_WGS84_TO_UTM32N, geom)


@dataclass
class NearestResult:
    distance_m: "float | None"
    tags: "dict | None" = None


class TaggedGeometryIndex:
    """STRtree wrapper that also remembers each geometry's OSM tags,
    since shapely's STRtree only returns geometries/indices, not
    arbitrary attached data."""

    def __init__(self, geoms_with_tags: "list[tuple[BaseGeometry, dict]]"):
        self._geoms = [g for g, _ in geoms_with_tags]
        self._tags = [t for _, t in geoms_with_tags]
        self._tree = STRtree(self._geoms) if self._geoms else None

    def __len__(self) -> int:
        return len(self._geoms)

    def nearest(self, point: BaseGeometry, *, max_distance_m: "float | None" = None) -> NearestResult:
        if self._tree is None:
            return NearestResult(distance_m=None)
        idx = self._tree.nearest(point)
        geom = self._geoms[idx]
        distance = point.distance(geom)
        if max_distance_m is not None and distance > max_distance_m:
            return NearestResult(distance_m=None)
        return NearestResult(distance_m=distance, tags=self._tags[idx])

    def within(self, buffer_polygon: BaseGeometry) -> "list[tuple[BaseGeometry, dict]]":
        if self._tree is None:
            return []
        idxs = self._tree.query(buffer_polygon, predicate="intersects")
        return [(self._geoms[i], self._tags[i]) for i in idxs]
