export type SortDirection = "asc" | "desc";

export type SortState<Column extends string> = {
  column: Column;
  direction: SortDirection;
};

export function nextSortState<Column extends string>(
  current: SortState<Column> | null,
  column: Column,
): SortState<Column> {
  if (!current || current.column !== column) {
    return { column, direction: "asc" };
  }

  return {
    column,
    direction: current.direction === "asc" ? "desc" : "asc",
  };
}

export function compareText(left: string, right: string) {
  return left.localeCompare(right, "ru", {
    numeric: true,
    sensitivity: "base",
  });
}

export function compareNumbers(left: number, right: number) {
  return left - right;
}
