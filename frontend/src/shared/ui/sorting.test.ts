import { describe, expect, it } from "vitest";

import { compareNumbers, compareText, nextSortState } from "./sorting";

describe("table sorting helpers", () => {
  it("starts ascending and toggles direction for the same column", () => {
    expect(nextSortState(null, "name")).toEqual({
      column: "name",
      direction: "asc",
    });
    expect(nextSortState({ column: "name", direction: "asc" }, "name")).toEqual(
      {
        column: "name",
        direction: "desc",
      },
    );
    expect(
      nextSortState({ column: "name", direction: "desc" }, "name"),
    ).toEqual({
      column: "name",
      direction: "asc",
    });
  });

  it("starts ascending again when another column is selected", () => {
    expect(
      nextSortState({ column: "name", direction: "desc" }, "warehouse"),
    ).toEqual({
      column: "warehouse",
      direction: "asc",
    });
  });

  it("compares text naturally and numbers numerically", () => {
    expect(compareText("SKU-2", "SKU-10")).toBeLessThan(0);
    expect(compareNumbers(2, 10)).toBeLessThan(0);
  });
});
