from enum import StrEnum


class TransferStatus(StrEnum):
    DRAFT = "draft"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"


class FbsReservationStatus(StrEnum):
    RESERVED = "reserved"
    CANCELLED = "cancelled"
    SHIPPED = "shipped"


class FboShipmentStatus(StrEnum):
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"


class OperationType(StrEnum):
    RECEIPT = "receipt"
    WAREHOUSE_CREATED = "warehouse_created"
    WAREHOUSE_RENAMED = "warehouse_renamed"
    WAREHOUSE_ARCHIVED = "warehouse_archived"
    TRANSFER_CREATED = "transfer_created"
    TRANSFER_DELETED = "transfer_deleted"
    TRANSFER_DISPATCHED = "transfer_dispatched"
    TRANSFER_RECEIVED = "transfer_received"
    FBS_RESERVED = "fbs_reserved"
    FBS_CANCELLED = "fbs_cancelled"
    FBS_SHIPPED = "fbs_shipped"
    FBO_DISPATCHED = "fbo_dispatched"
    FBO_RECEIVED = "fbo_received"
