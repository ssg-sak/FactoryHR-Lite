export function finiteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function formatNumber(value: unknown, digits = 0): string {
  const parsed = finiteNumber(value);
  if (parsed === null) {
    return "—";
  }
  return parsed.toLocaleString("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value: unknown): string {
  const parsed = finiteNumber(value);
  if (parsed === null) {
    return "—";
  }
  return `${formatNumber(parsed, 2)}%`;
}

export function formatHours(value: unknown): string {
  return `${formatNumber(value, 2)}시간`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) {
    return value;
  }
  return `${year}.${month}.${day}`;
}

export function monthsBetween(from: string, to: string): number | null {
  const start = Date.parse(from);
  const end = Date.parse(to);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) {
    return null;
  }
  return (end - start) / (1000 * 60 * 60 * 24) / 30.4375;
}

export function formatTenure(hiredAt: string, resignedAt: string | null, asOf: string): string {
  const months = monthsBetween(hiredAt, resignedAt ?? asOf);
  if (months === null) {
    return "—";
  }
  return `${formatNumber(months, 1)}개월`;
}

export function hasChartValues(values: Array<number | null | undefined>): boolean {
  return values.some((value) => finiteNumber(value) !== null);
}
