# UPIT 5: Analiza najvrednijih transakcija (Jul 2023)

---

## 1. KOD UPITA

*Prikazuje 5 najvrednijih transakcija u julu 2023. godine, zajedno sa detaljima o prodavnici, načinu plaćanja i kupljenim proizvodima.*

```javascript
db.getCollection('transactions').aggregate([
  {
    $match: {
      created_at: {
        $gte: ISODate("2023-07-01T00:00:00.000Z"),
        $lt: ISODate("2023-08-01T00:00:00.000Z")
      }
    }
  },
  {
    $sort: { "amounts.final": -1 }
  },
  {
    $limit: 5
  },
  {
    $lookup: {
      from: "stores",
      localField: "store_id",
      foreignField: "_id",
      as: "store_details"
    }
  },
  {
    $lookup: {
      from: "payment_methods",
      localField: "payment_method_id",
      foreignField: "_id",
      as: "payment_details"
    }
  },
  {
    $lookup: {
      from: "transaction_items",
      localField: "_id",
      foreignField: "transaction_id",
      as: "items_sold"
    }
  },
  {
    $unwind: { path: "$items_sold" }
  },
  {
    $lookup: {
      from: "menu_items",
      localField: "items_sold.menu_item_id",
      foreignField: "_id",
      as: "menu_item_details"
    }
  },
  {
    $group: {
      _id: "$_id",
      final_amount: { $first: "$amounts.final" },
      store_name: { $first: { $arrayElemAt: ["$store_details.name", 0] } },
      payment_method: { $first: { $arrayElemAt: ["$payment_details.method_name", 0] } },
      products_purchased: { $push: { $arrayElemAt: ["$menu_item_details.name", 0] } }
    }
  },
  {
    $sort: { final_amount: -1 }
  }
], { allowDiskUse: true })
```
## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja (executionTimeMillis):** 15,418 ms  
- **Ukupno pregledanih dokumenata (totalDocsExamined):** 1,240,630  
- **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** 10  
- **Strategija izvršavanja:** COLLSCAN praćen sa SORT, a zatim višestruki EQ_LOOKUP (Index Lookups).

## 3. REZULTAT UPITA

```json
[
  {
    "_id": "69807d5d-0eaf-411d-ad7f-c786dc5c373b",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 89q",
    "payment_method": "debit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "d9430ed6-6862-4384-8500-ac2e394d8089",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 57W",
    "payment_method": "credit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "0e569659-fb7b-4c89-8233-9434ca9d4a28",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 57W",
    "payment_method": "cash",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "2346bcfd-520f-43ba-9599-43934670dfc3",
    "final_amount": "90.0",
    "store_name": "G Coffee @ Kondominium Putra",
    "payment_method": "grabpay",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "e1a90e02-bd3d-4425-a551-3a8c6059c5f2",
    "final_amount": "90.0",
    "store_name": "G Coffee @ Alam Tun Hussein Onn",
    "payment_method": "credit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  }
]
```

## 4. ZAKLJUČAK

**Performanse:**  
Upit se izvršio za 15.4 sekunde. Plan izvršavanja pokazuje da je početna faza morala da izvrši COLLSCAN na preko 620,000 transakcija i da ih zatim sortira u memoriji. Ovo je glavno "usko grlo" koje uzrokuje dugo vreme izvršavanja.

**Poslovni uvid:**  
Najvrednije transakcije u julu 2023. su imale vrednost od 90.0. Zanimljivo je da sve one sadrže isključivo "Matcha Latte" u velikim količinama, što može ukazivati na grupne kupovine ili posebnu popularnost ovog proizvoda.
