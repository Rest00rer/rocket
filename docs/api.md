# Предварительные API-контракты

Префикс всех маршрутов: `/api`.

| Метод   | Путь                                  | Назначение |
| ------- | ------------------------------------- | ---------- |
| GET     | `/health`                             | liveness |
| GET     | `/health/ready`                       | проверка PostgreSQL |
| GET     | `/inventory`                          | сводка остатков и пути |
| GET     | `/products`                           | товары |
| GET     | `/warehouses`                         | активные и архивные ФФ |
| POST    | `/warehouses`                         | создать ФФ |
| PATCH   | `/warehouses/{id}`                    | переименовать ФФ |
| DELETE  | `/warehouses/{id}`                    | архивировать ФФ |
| GET     | `/operations`                         | история и фильтры |
| POST    | `/receipts`                           | оформить приход |
| POST    | `/transfers`                          | создать перемещение |
| GET     | `/transfers`                          | список перемещений |
| POST    | `/transfers/{id}/dispatch`            | отправить между ФФ |
| POST    | `/transfers/{id}/receive`             | принять на ФФ |
| POST    | `/fbs/reservations`                   | зарезервировать |
| GET     | `/fbs/reservations`                   | список FBS-резервов |
| POST    | `/fbs/reservations/{id}/cancel`       | отменить резерв |
| POST    | `/fbs/reservations/{id}/ship`         | отправить клиенту |
| POST    | `/fbo/shipments`                      | отправить на маркетплейс |
| GET     | `/fbo/shipments`                      | список FBO-отправок |
| POST    | `/fbo/shipments/{id}/receive`         | подтвердить приёмку |

## Общий формат команды

```http
Idempotency-Key: 7b783aa8-6175-4c8f-854a-e4f6de729d27
Content-Type: application/json
```

```json
{
  "product_id": "uuid",
  "warehouse_id": "uuid",
  "quantity": 3
}
```

Успешное создание возвращает `201`, переход состояния — `200`, ошибка
валидации — `422`, конфликт состояния/остатка — `409`, отсутствие сущности —
`404`.

## Сводка остатков

```json
{
  "items": [
    {
      "product": {"id": "uuid", "sku": "SKU-101", "name": "Органайзер"},
      "warehouse": {"id": "uuid", "name": "Север", "archived": false},
      "on_hand": 10,
      "reserved_fbs": 2,
      "available": 8
    }
  ],
  "in_transit": {
    "between_warehouses": 4,
    "fbo": 3,
    "fbs_to_customer": 2
  },
  "transit_items": []
}
```

## Ошибка

```json
{
  "code": "insufficient_stock",
  "message": "На выбранном складе недостаточно товара",
  "details": {},
  "request_id": "uuid"
}
```

