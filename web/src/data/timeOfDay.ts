// Buckets event_hour into everyday parts of the day, not equal-width
// clock ranges — "orario di pranzo" matters more to a reader than a
// mechanical 3-hour slice would. Order here is chronological and is
// reused as the display order in TimeOfDayChart.
export interface TimeOfDayBucket {
  id: string;
  label: string;
  hours: number[];
}

export const TIME_OF_DAY_BUCKETS: TimeOfDayBucket[] = [
  { id: "notte", label: "Notte", hours: [23, 0, 1, 2, 3, 4, 5] },
  { id: "primo_mattino", label: "Primo mattino", hours: [6, 7] },
  { id: "mattino", label: "Mattino", hours: [8, 9, 10] },
  { id: "pranzo", label: "Orario di pranzo", hours: [11, 12, 13] },
  { id: "primo_pomeriggio", label: "Primo pomeriggio", hours: [14, 15, 16] },
  { id: "pomeriggio", label: "Pomeriggio", hours: [17, 18] },
  { id: "sera", label: "Sera", hours: [19, 20, 21, 22] },
];

const HOUR_TO_BUCKET: Record<number, string> = {};
for (const bucket of TIME_OF_DAY_BUCKETS) {
  for (const hour of bucket.hours) HOUR_TO_BUCKET[hour] = bucket.id;
}

export function bucketForHour(hour: number): string | null {
  return HOUR_TO_BUCKET[hour] ?? null;
}
