import { DEFAULT_DATE_FROM, DEFAULT_DATE_TO } from "./constants";
import type { WorkforceFilters } from "./types";

export const INITIAL_WORKFORCE_FILTERS: WorkforceFilters = {
  date_from: DEFAULT_DATE_FROM,
  date_to: DEFAULT_DATE_TO,
};

export function resetWorkforceFilters(): WorkforceFilters {
  return { ...INITIAL_WORKFORCE_FILTERS };
}
