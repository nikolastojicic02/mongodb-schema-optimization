# Šema baze podataka - Verzija V1 (normalizovana šema)

Ovaj dokument opisuje strukturu baze podataka `coffee_db_v1`. Ova šema je dizajnirana po principu **normalizacije**, slično relacionim bazama podataka. Podaci su razdvojeni u više logičkih kolekcija kako bi se smanjila redundansa i osigurala konzistentnost.

## Pregled kolekcija

Baza se sastoji od sledećih 7 kolekcija:

-   **Statičke (lookup) kolekcije:**
    1.  `stores` - Podaci o prodavnicama.
    2.  `menu_items` - Podaci o artiklima sa menija.
    3.  `payment_methods` - Podaci o načinima plaćanja.
    4.  `vouchers` - Podaci o dostupnim vaučerima.
-   **Dinamičke (transakcione) kolekcije:**
    5.  `users` - Podaci o registrovanim korisnicima.
    6.  `transactions` - Glavni dokument za svaku transakciju.
    7.  `transaction_items` - Pojedinačne stavke za svaku transakciju.

---

## Detaljan prikaz kolekcija

### 1. `stores`

Čuva statičke podatke o svim prodavnicama.

```json
{
  "_id": 1, // Integer, Store ID
  "name": "Coffee Corner Downtown", // String
  "address": { // Ugnježdeni dokument
    "street": "123 Main St",
    "city": "Metropolis",
    "postal_code": "10001",
    "state": "NY"
  },
  "location": { // GeoJSON tačka za geoprostorne upite
    "type": "Point",
    "coordinates": [-74.0060, 40.7128] // [longitude, latitude]
  }
}
```

### 2. `menu_items`

Čuva statičke podatke o svim artiklima koji se mogu prodati.


```json
{
  "_id": 101, // Integer, Item ID
  "name": "Espresso", // String
  "category": "Coffee", // String
  "price": "2.50" // BSON Decimal128
}
```

### 3. `payment_methods`


Čuva statičke podatke o načinima plaćanja.

```json
{
  "_id": 1, // Integer, Method ID
  "method_name": "Credit Card", // String
  "category": "Card" // String
}
```

### 4. `vouchers`

Čuva statičke podatke o promotivnim vaučerima.

```json
{
  "_id": 1, // Integer, Voucher ID
  "voucher_code": "SUMMER10", // String
  "discount_type": "percentage", // String
  "discount_value": "10.0", // BSON Decimal128
  "valid_from": "2024-06-01T00:00:00.000Z", // BSON DateTime
  "valid_to": "2024-08-31T23:59:59.000Z" // BSON DateTime
}
```

### 5. `users`

Čuva podatke o korisnicima koji su se registrovali.

```json
{
  "_id": 1, // Integer, User ID
  "gender": "Female", // String
  "birthdate": "1990-05-15T00:00:00.000Z", // BSON DateTime
  "registered_at": "2023-07-01T10:30:00.000Z" // BSON DateTime
}
```

### 6. `transactions`

Centralna kolekcija koja povezuje sve delove jedne kupovine.

```json
{
  "_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // String (UUID)
  "store_id": 1, // Integer, Referenca na kolekciju `stores`
  "user_id": 123, // Integer, Referenca na kolekciju `users` (može biti null)
  "payment_method_id": 1, // Integer, Referenca na kolekciju `payment_methods`
  "voucher_id": 5, // Integer, Referenca na kolekciju `vouchers` (može biti null)
  "amounts": { // Ugnježdeni dokument
    "original": "15.75", // BSON Decimal128
    "discount": "1.57", // BSON Decimal128
    "final": "14.18" // BSON Decimal128
  },
  "created_at": "2023-07-15T14:45:10.000Z" // BSON DateTime
}
```

### 7. `transaction_items`

Čuva svaku pojedinačnu stavku prodatu u okviru jedne transakcije. Ovo je primer relacije "jedan-prema-više".

```json
{
  "_id": ObjectId("..."), // Automatski generisan ID
  "transaction_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // String, Referenca na `transactions`
  "menu_item_id": 101, // Integer, Referenca na `menu_items`
  "quantity": 2, // Integer
  "unit_price": "2.50", // BSON Decimal128
  "subtotal": "5.00" // BSON Decimal128
}
```

## Relacije između kolekcija

Veze između kolekcija se uspostavljaju putem referenci (slično "stranim ključevima" u SQL-u). Za dobijanje kompletnih informacija, potrebno je koristiti `$lookup` agregacionu fazu (MongoDB ekvivalent za `JOIN`).

-   `transactions.store_id` **->** `stores._id`
-   `transactions.user_id` **->** `users._id`
-   `transactions.payment_method_id` **->** `payment_methods._id`
-   `transactions.voucher_id` **->** `vouchers._id`
-   `transaction_items.transaction_id` **->** `transactions._id`
-   `transaction_items.menu_item_id` **->** `menu_items._id`