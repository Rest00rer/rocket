export const viewIds = [
  "inventory",
  "operations",
  "history",
  "warehouses",
] as const;

export type ViewId = (typeof viewIds)[number];

export function parseViewHash(hash: string): {
  view: ViewId;
  params: URLSearchParams;
} {
  const [candidate, query = ""] = hash.replace(/^#/, "").split("?", 2);
  const view = viewIds.includes(candidate as ViewId)
    ? (candidate as ViewId)
    : "inventory";
  return { view, params: new URLSearchParams(query) };
}

function viewHref(view: ViewId, values: Record<string, string | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return `#${view}${query ? `?${query}` : ""}`;
}

export function historyHref(
  values: {
    sku?: string;
    warehouseId?: string;
    group?: string;
  } = {},
) {
  return viewHref("history", {
    sku: values.sku,
    warehouse_id: values.warehouseId,
    group: values.group,
  });
}

export function inventoryHref(sku?: string) {
  return viewHref("inventory", { sku });
}

export function warehouseHref(warehouseId?: string) {
  return viewHref("warehouses", { warehouse_id: warehouseId });
}
