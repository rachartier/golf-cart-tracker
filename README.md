# Golf cart Tracker API

This API allows you to track golf carts in real-time. It provides endpoints to update the location and status of golf carts, retrieve their historical data, and receive real-time updates via WebSocket.

## Features

- **Update cart Information**: Update the location, status, and battery level of a golf cart.
- **Retrieve cart Information**: Retrieve historical data of a golf cart.
- **Retrieve Today's Data**: Retrieve today's data for all golf carts.
- **Real-Time Updates**: Receive real-time updates via WebSocket.

## Endpoints

### Update cart Information

**PUT** `/carts/{cart_id}`

Update the location, status, and battery level of a golf cart.

#### Request Body

```json
{
  "latitude": 12.34,
  "longitude": 56.78,
  "status": 1,
  "battery": 80,
  "at_home": false
}
```

#### Response

```json
{
  "latitude": 12.34,
  "longitude": 56.78,
  "status": 1,
  "battery": 80,
  "at_home": false
}
```

### Retrieve cart Information

**GET** `/cart/{cart_id}`

Retrieve historical data of a golf cart.

#### Query Parameters

- `count` (optional): Number of records to retrieve. Default is 10.

#### Response

```json
[
  {
    "latitude": 12.34,
    "longitude": 56.78,
    "status": 1,
    "battery": 80,
    "at_home": false
  },
  ...
]
```

### Retrieve Today's Data

**GET** `/carts/today`

Retrieve today's data for all golf carts.

#### Query Parameters

- `count_by_cart` (optional): Number of records to retrieve per cart. Default is 10.

#### Response

```json
{
  "cart_id_1": [
    {
      "latitude": 12.34,
      "longitude": 56.78,
      "status": 1,
      "battery": 80,
      "at_home": false
    },
    ...
  ],
  "cart_id_2": [
    {
      "latitude": 23.45,
      "longitude": 67.89,
      "status": 2,
      "battery": 60,
      "at_home": false
    },
    ...
  ]
}
```

### Delete cart Information

**DELETE** `/carts/{cart_id}`

Delete all records of a specific golf cart.

### Delete all carts information

**DELETE** `/carts`

Delete all records of all golf carts.

#### Response

```json
{
  "message": "cart deleted",
  "deleted_points": 10
}
```

### Real-Time Updates

**WebSocket** `/ws`

Receive real-time updates of golf cart data.

#### Message Format

```json
{
  "id": "cart_id",
  "latitude": 12.34,
  "longitude": 56.78,
  "status": 1,
  "battery": 80,
  "at_home": false
}
```

## License

This project is licensed under the MIT License.
