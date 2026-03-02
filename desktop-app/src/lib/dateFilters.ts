// Canonical date filter values used when building ICA command arguments.
export interface DateFilterState {
    fromDate: string;
    toDate: string;
}

// Two-digit padding keeps month/day values in ISO-compatible shape.
const TIME_UNIT_PAD_LENGTH = 2;

// Normalizes numeric date units to two characters (e.g., 3 -> 03).
function padTimeUnit(value: number): string {
    return String(value).padStart(TIME_UNIT_PAD_LENGTH, '0');
}

// Accepts either YYYY-MM-DD or M/D/YYYY and returns normalized YYYY-MM-DD.
export function normalizeDateInput(value: string): string | null {
    const trimmed = value.trim();
    if (!trimmed) return null;

    const isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
    if (isoMatch) return trimmed;

    const slashMatch = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(trimmed);
    if (slashMatch) {
        const month = padTimeUnit(Number(slashMatch[1]));
        const day = padTimeUnit(Number(slashMatch[2]));
        return `${slashMatch[3]}-${month}-${day}`;
    }

    return null;
}

// Converts filter state into optional ICA CLI flags.
export function buildDateFilterArgs(filters: DateFilterState): string[] {
    const args: string[] = [];
    const fromValue = normalizeDateInput(filters.fromDate);
    const toValue = normalizeDateInput(filters.toDate);

    if (fromValue) {
        args.push('--from-date', fromValue);
    }
    if (toValue) {
        args.push('--to-date', toValue);
    }

    return args;
}
