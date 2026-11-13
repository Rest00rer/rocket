import { describe, expect, it } from "vitest";

import {
  historyHref,
  inventoryHref,
  operationsHref,
  parseViewHash,
  warehouseHref,
} from "./navigation";

describe("navigation links", () => {
  it("parses a view and its filters", () => {
    const location = parseViewHash("#history?sku=SKU-101&group=fbs");

    expect(location.view).toBe("history");
    expect(location.params.get("sku")).toBe("SKU-101");
    expect(location.params.get("group")).toBe("fbs");
  });

  it("falls back to inventory for an unknown view", () => {
    expect(parseViewHash("#unknown").view).toBe("inventory");
  });

  it("builds encoded entity links", () => {
    expect(historyHref({ sku: "SKU 101", group: "fbs" })).toBe(
      "#history?sku=SKU+101&group=fbs",
    );
    expect(inventoryHref("SKU-101")).toBe("#inventory?sku=SKU-101");
    expect(operationsHref("fbs-to-customer")).toBe(
      "#operations?section=fbs-to-customer",
    );
    expect(warehouseHref("warehouse-id")).toBe(
      "#warehouses?warehouse_id=warehouse-id",
    );
  });
});
