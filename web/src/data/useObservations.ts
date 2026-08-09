import { useEffect, useState } from "react";
import type { ObservationCollection, ObservationFeature } from "./types";

export interface ObservationsState {
  loading: boolean;
  error: string | null;
  features: ObservationFeature[];
}

// Loads the pipeline's precalculated GeoJSON as a static asset. This is
// the ONLY data-fetching the frontend does: no client-side GIS, no
// recomputation of anything the pipeline already derived (AGENTS.md).
export function useObservations(): ObservationsState {
  const [state, setState] = useState<ObservationsState>({
    loading: true,
    error: null,
    features: [],
  });

  useEffect(() => {
    let cancelled = false;

    fetch(`${import.meta.env.BASE_URL}data/observations.geojson`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status} while loading observations.geojson`);
        }
        return res.json() as Promise<ObservationCollection>;
      })
      .then((data) => {
        if (!cancelled) {
          setState({ loading: false, error: null, features: data.features });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : String(err);
          setState({ loading: false, error: message, features: [] });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

// Days between an ISO event_date and now; null when the date isn't usable
// (see date_parse_status) rather than defaulting to "0 = recent", which
// would fabricate recency for an unknown date.
export function daysSinceEvent(eventDateIso: string | null): number | null {
  if (!eventDateIso) return null;
  const eventDate = new Date(eventDateIso);
  if (Number.isNaN(eventDate.getTime())) return null;
  const diffMs = Date.now() - eventDate.getTime();
  return Math.max(0, diffMs / (1000 * 60 * 60 * 24));
}
