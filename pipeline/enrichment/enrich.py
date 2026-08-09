"""Milestone 8: per-observation OSM enrichment.

Computes distance/count/length indicators separately per road category,
building, settlement and tourism-feature layer — deliberately never
combined into a single opaque "humanization score" (see README.md,
"Antropizzazione: niente indice opaco all'inizio").

Buffers are capped at 250/500 m for roads and buildings, and 1000 m for
the sparser tourism layer, matching the fetch radii documented in
osm_source.py — a disclosed MVP scope reduction from the 250/500/1000 m
originally envisioned for every layer (see that module's docstring for
why). Any "distance_to_*_m" field is `None`, never a guessed value, when
nothing of that type was found within the fetch's search radius.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon

from pipeline.enrichment.osm_source import OsmPoint, OsmWay
from pipeline.enrichment.spatial import TaggedGeometryIndex, to_utm32n

MAJOR_ROAD_VALUES = {"motorway", "trunk", "primary", "secondary"}
MINOR_ROAD_VALUES = {"tertiary", "residential", "service", "unclassified"}
TRACK_VALUES = {"track"}
PATH_VALUES = {"path", "footway"}

BUFFER_RADII_M = (250, 500)
TOURISM_BUFFER_RADIUS_M = 1000


def _way_to_line(way: OsmWay) -> "LineString | None":
    if len(way.coordinates) < 2:
        return None
    return LineString(way.coordinates)


def _way_to_polygon(way: OsmWay) -> "Polygon | None":
    coords = way.coordinates
    if len(coords) < 4 or coords[0] != coords[-1]:
        # Not a closed way: can't form a valid building polygon from it.
        # Documented limitation, not a silent guess.
        return None
    try:
        poly = Polygon(coords)
    except Exception:
        return None
    return poly if poly.is_valid and not poly.is_empty else None


@dataclass
class OsmIndices:
    major_roads: TaggedGeometryIndex
    minor_roads: TaggedGeometryIndex
    tracks: TaggedGeometryIndex
    paths: TaggedGeometryIndex
    all_roads: TaggedGeometryIndex  # major + minor, i.e. vehicular roads
    buildings: TaggedGeometryIndex
    settlements: TaggedGeometryIndex
    tourism: TaggedGeometryIndex


def build_indices(
    roads: "list[OsmWay]",
    buildings: "list[OsmWay]",
    settlements: "list[OsmPoint]",
    tourism: "list[OsmPoint]",
) -> OsmIndices:
    def _bucket(values: set) -> list:
        out = []
        for way in roads:
            if way.tags.get("highway") not in values:
                continue
            line = _way_to_line(way)
            if line is not None:
                out.append((to_utm32n(line), way.tags))
        return out

    major = _bucket(MAJOR_ROAD_VALUES)
    minor = _bucket(MINOR_ROAD_VALUES)
    track = _bucket(TRACK_VALUES)
    path = _bucket(PATH_VALUES)

    building_geoms = []
    for way in buildings:
        poly = _way_to_polygon(way)
        if poly is not None:
            building_geoms.append((to_utm32n(poly), way.tags))

    settlement_geoms = [(to_utm32n(Point(p.lon, p.lat)), p.tags) for p in settlements]
    tourism_geoms = [(to_utm32n(Point(p.lon, p.lat)), p.tags) for p in tourism]

    return OsmIndices(
        major_roads=TaggedGeometryIndex(major),
        minor_roads=TaggedGeometryIndex(minor),
        tracks=TaggedGeometryIndex(track),
        paths=TaggedGeometryIndex(path),
        all_roads=TaggedGeometryIndex(major + minor),
        buildings=TaggedGeometryIndex(building_geoms),
        settlements=TaggedGeometryIndex(settlement_geoms),
        tourism=TaggedGeometryIndex(tourism_geoms),
    )


@dataclass
class EnrichedFields:
    distance_to_major_road_m: "float | None" = None
    distance_to_any_road_m: "float | None" = None
    distance_to_track_m: "float | None" = None
    distance_to_path_m: "float | None" = None
    road_length_250m: "float | None" = None
    road_length_500m: "float | None" = None
    path_length_250m: "float | None" = None
    path_length_500m: "float | None" = None
    distance_to_building_m: "float | None" = None
    buildings_250m: "int | None" = None
    buildings_500m: "int | None" = None
    building_area_250m: "float | None" = None
    building_area_500m: "float | None" = None
    distance_to_settlement_m: "float | None" = None
    nearest_settlement_type: "str | None" = None
    nearest_settlement_name: "str | None" = None
    tourism_features_1000m: "int | None" = None


def _length_within(index: TaggedGeometryIndex, buffer_polygon) -> float:
    total = 0.0
    for geom, _ in index.within(buffer_polygon):
        total += geom.intersection(buffer_polygon).length
    return total


def _buildings_within(index: TaggedGeometryIndex, buffer_polygon) -> "tuple[int, float]":
    count = 0
    area = 0.0
    for geom, _ in index.within(buffer_polygon):
        count += 1
        area += geom.intersection(buffer_polygon).area
    return count, area


def enrich_point(
    lon: float,
    lat: float,
    indices: OsmIndices,
    *,
    road_search_radius_m: float,
    building_search_radius_m: float,
    settlement_search_radius_m: float,
) -> EnrichedFields:
    point_utm = to_utm32n(Point(lon, lat))
    fields = EnrichedFields()

    fields.distance_to_major_road_m = indices.major_roads.nearest(
        point_utm, max_distance_m=road_search_radius_m
    ).distance_m
    fields.distance_to_any_road_m = indices.all_roads.nearest(
        point_utm, max_distance_m=road_search_radius_m
    ).distance_m
    fields.distance_to_track_m = indices.tracks.nearest(
        point_utm, max_distance_m=road_search_radius_m
    ).distance_m
    fields.distance_to_path_m = indices.paths.nearest(
        point_utm, max_distance_m=road_search_radius_m
    ).distance_m
    fields.distance_to_building_m = indices.buildings.nearest(
        point_utm, max_distance_m=building_search_radius_m
    ).distance_m

    nearest_settlement = indices.settlements.nearest(
        point_utm, max_distance_m=settlement_search_radius_m
    )
    fields.distance_to_settlement_m = nearest_settlement.distance_m
    if nearest_settlement.tags:
        fields.nearest_settlement_type = nearest_settlement.tags.get("place")
        fields.nearest_settlement_name = nearest_settlement.tags.get("name")

    for radius in BUFFER_RADII_M:
        buf = point_utm.buffer(radius)
        road_len = _length_within(indices.all_roads, buf)
        path_len = _length_within(indices.paths, buf) + _length_within(indices.tracks, buf)
        count, area = _buildings_within(indices.buildings, buf)
        setattr(fields, f"road_length_{radius}m", road_len)
        setattr(fields, f"path_length_{radius}m", path_len)
        setattr(fields, f"buildings_{radius}m", count)
        setattr(fields, f"building_area_{radius}m", area)

    tourism_buf = point_utm.buffer(TOURISM_BUFFER_RADIUS_M)
    fields.tourism_features_1000m = len(indices.tourism.within(tourism_buf))

    return fields
