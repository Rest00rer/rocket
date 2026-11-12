export type Product = {
  id: string;
  sku: string;
  name: string;
};

export type Warehouse = {
  id: string;
  name: string;
  archived_at: string | null;
  archived: boolean;
};

export type InventoryItem = {
  product: Product;
  warehouse: Warehouse;
  on_hand: number;
  reserved_fbs: number;
  available: number;
};

export type TransitItem = {
  kind: string;
  product: Product;
  quantity: number;
  source: Warehouse | null;
  destination: Warehouse | null;
  status: string;
};

export type InventorySummary = {
  items: InventoryItem[];
  in_transit: {
    between_warehouses: number;
    fbo: number;
    fbs_to_customer: number;
  };
  transit_items: TransitItem[];
};

export type Transfer = {
  id: string;
  product_id: string;
  source_warehouse_id: string;
  destination_warehouse_id: string;
  quantity: number;
  status: "draft" | "in_transit" | "received";
  created_at: string;
  dispatched_at: string | null;
  received_at: string | null;
};

export type FbsReservation = {
  id: string;
  product_id: string;
  warehouse_id: string;
  quantity: number;
  status: "reserved" | "cancelled" | "shipped";
  created_at: string;
  cancelled_at: string | null;
  shipped_at: string | null;
};

export type FboShipment = {
  id: string;
  product_id: string;
  warehouse_id: string;
  quantity: number;
  status: "in_transit" | "received";
  created_at: string;
  received_at: string | null;
};

export type Operation = {
  id: string;
  operation_type: string;
  product_id: string | null;
  sku: string | null;
  product_name: string | null;
  quantity: number | null;
  source_warehouse_id: string | null;
  source_warehouse_name: string | null;
  destination_warehouse_id: string | null;
  destination_warehouse_name: string | null;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

export type OperationList = { items: Operation[] };

export type DomainErrorBody = {
  code?: string;
  message?: string;
  details?: {
    available_here?: number;
    available_total?: number;
    alternatives?: Array<{
      warehouse_id?: string;
      name?: string;
      available?: number;
    }>;
  };
};

export type DashboardData = {
  products: Product[];
  warehouses: Warehouse[];
  inventory: InventorySummary;
  transfers: Transfer[];
  fbs: FbsReservation[];
  fbo: FboShipment[];
  operations: Operation[];
};
