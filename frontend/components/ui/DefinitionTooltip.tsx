"use client";

import { Info } from "lucide-react";
import { useId, useState } from "react";

export function DefinitionTooltip({ definition }: { definition: string }) {
  const id = useId();
  const [open, setOpen] = useState(false);

  return (
    <span
      className="relative inline-flex shrink-0"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="rounded p-0.5 text-slate-400 hover:bg-slate-50 hover:text-slate-600"
        aria-label="지표 정의"
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
      >
        <Info size={14} strokeWidth={2} aria-hidden="true" />
      </button>
      {open ? (
        <span
          id={id}
          role="tooltip"
          className="absolute right-0 top-full z-20 mt-1 w-72 rounded border border-slate-200 bg-white p-3 text-left shadow-sm"
        >
          <span className="mb-1 block text-[11px] font-medium text-slate-500">지표 정의</span>
          <span className="whitespace-pre-wrap text-xs leading-5 text-slate-700">{definition}</span>
        </span>
      ) : null}
    </span>
  );
}
