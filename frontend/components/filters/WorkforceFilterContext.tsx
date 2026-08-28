"use client";

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { INITIAL_WORKFORCE_FILTERS, resetWorkforceFilters } from "@/lib/workforce-filters";
import type { WorkforceFilters } from "@/lib/types";

const WorkforceFilterContext = createContext<{
  filters: WorkforceFilters;
  setFilters: (next: WorkforceFilters) => void;
  resetFilters: () => void;
} | null>(null);

export function WorkforceFilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<WorkforceFilters>(INITIAL_WORKFORCE_FILTERS);
  const value = useMemo(
    () => ({
      filters,
      setFilters,
      resetFilters: () => setFilters(resetWorkforceFilters()),
    }),
    [filters],
  );
  return <WorkforceFilterContext.Provider value={value}>{children}</WorkforceFilterContext.Provider>;
}

export function useWorkforceFilters() {
  const context = useContext(WorkforceFilterContext);
  if (!context) {
    throw new Error("useWorkforceFilters must be used within WorkforceFilterProvider");
  }
  return context;
}
