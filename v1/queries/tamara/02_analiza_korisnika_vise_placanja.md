# UPIT 2: Analiza korisnika sa više metoda plaćanja

---

## 1. KOD UPITA

*Identifikuje korisnike koji koriste više od jedne metode plaćanja, analizirajući njihov pol, prosečnu vrednost transakcije i ukupan broj transakcija.*

```javascript
db.getCollection('transactions').aggregate([
  {
    $match: {
      user_id: { $ne: null } // Fokusira se samo na registrovane korisnike
    }
  },
  {
    $group: {
      _id: "$user_id",
      uniquePaymentMethods: { $addToSet: "$payment_method_id" }, // Sakuplja jedinstvene metode plaćanja
      totalTransactions: { $sum: 1 },
      totalSpend: { $sum: "$amounts.final" }
    }
  },
  {
    $match: {
      $expr: { $gte: [{ $size: "$uniquePaymentMethods" }, 2] } // Filtrira korisnike sa 2+ metode plaćanja
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "_id",
      foreignField: "_id",
      as: "userDetails"
    }
  },
  {
    $unwind: "$userDetails"
  },
  {
    $project: {
      _id: 0,
      user_id: "$_id",
      user_gender: "$userDetails.gender",
      number_of_payment_methods: { $size: "$uniquePaymentMethods" },
      average_transaction_value: { $round: [{ $divide: ["$totalSpend", "$totalTransactions"] }, 2] },
      total_transactions: "$totalTransactions"
    }
  },
  {
    $sort: {
      number_of_payment_methods: -1,
      average_transaction_value: -1
    }
  }
])
```

---

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

-   **Vreme izvršavanja (executionTimeMillis):** `3093 ms`
-   **Ukupno pregledanih dokumenata (totalDocsExamined):** `1240620`
-   **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** `0`
-   **Strategija izvršavanja:** `COLLSCAN` na `transactions` kolekciji.

---

## 3. REZULTAT UPITA

```json
[
  {
    "user_id": 8,
    "user_gender": "female",
    "number_of_payment_methods": 5,
    "average_transaction_value": "47.36",
    "total_transactions": 7
  },
  {
    "user_id": 148,
    "user_gender": "male",
    "number_of_payment_methods": 5,
    "average_transaction_value": "44.64",
    "total_transactions": 6
  }
]
```

## 4. ZAKLJUČAK

### Performanse
Vreme izvršavanja od **3 sekunde** je relativno sporo.  
Problem je **COLLSCAN** nad **1.24 miliona dokumenata** jer ne postoji indeks na polju **`user_id`**.  
Kreiranje **sparse indeksa** bi dramatično ubrzalo operaciju.

### Poslovni uvid
Upit uspešno identifikuje **tehnološki fleksibilne korisnike**.  
Rezultati na vrhu prikazuju kupce koji ne samo da koriste **sve opcije plaćanja (5)**,  
već imaju i **visoku prosečnu potrošnju**.  
Oni su idealni kandidati za **marketinške kampanje** i **testiranje novih tehnologija**.
