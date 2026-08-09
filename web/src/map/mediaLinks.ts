// Classifies pipeline-extracted media_links (see
// pipeline.normalization.kml_parser._media_links, sourced from the KML's
// ExtendedData/gx_media_links) into images vs. YouTube videos, so the
// point detail popup can render each appropriately instead of treating
// every link as an <img> (which silently breaks for a YouTube URL).
const YOUTUBE_ID_RE = /youtube\.com\/(?:embed\/|watch\?v=)([a-zA-Z0-9_-]+)/;

export type MediaItem =
  | { kind: "youtube"; videoId: string; url: string }
  | { kind: "image"; url: string };

export function classifyMediaLinks(links: string[]): MediaItem[] {
  return links.map((url) => {
    const match = url.match(YOUTUBE_ID_RE);
    if (match) {
      return { kind: "youtube", videoId: match[1], url };
    }
    return { kind: "image", url };
  });
}
