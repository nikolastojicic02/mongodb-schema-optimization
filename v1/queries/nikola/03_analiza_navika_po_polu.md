# UPIT 3: Analiza potrošačkih navika po polu

---

## 1. KOD UPITA

*Pruža detaljnu analizu i poređenje potrošačkih navika između muških i ženskih korisnika.*

```javascript
db.getCollection('transactions').aggregate([
  {
    $match: {
      user_id: { $ne: null }
    }
  },
  {
    $lookup: {
      from: "users",
      localField: "user_id",
      foreignField: "_id",
      as: "userDetails"
    }
  },
  {
    $unwind: {
      path: "$userDetails",
      preserveNullAndEmptyArrays: false
    }
  },
  {
    $group: {
      _id: "$userDetails.gender",
      totalSpend: { $sum: "$amounts.final" },
      totalTransactions: { $sum: 1 },
      totalUsers: { $addToSet: "$user_id" }
    }
  },
  {
    $project: {
      _id: 0,
      gender: "$_id",
      total_spend: { $round: ["$totalSpend", 2] },
      total_transactions: "$totalTransactions",
      number_of_users: { $size: "$totalUsers" },
      average_transaction_value: { $round: [{ $divide: ["$totalSpend", "$totalTransactions"] }, 2] },
      average_transactions_per_user: { $round: [{ $divide: ["$totalTransactions", { $size: "$totalUsers" }] }, 2] }
    }
  },
  {
    $sort: {
      gender: 1
    }
  }
])
```
## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja (executionTimeMillis):** 6,761 ms  
- **Ukupno pregledanih dokumenata (totalDocsExamined):** 1,240,620  
- **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** 0  
- **Strategija izvršavanja:** COLLSCAN na svih ~1.24 miliona dokumenata u `transactions` kolekciji.

## 3. REZULTAT UPITA

```json
[
  {
    "gender": "female",
    "total_spend": "335018.22",
    "total_transactions": 10087,
    "number_of_users": 6025,
    "average_transaction_value": "33.21",
    "average_transactions_per_user": 1.67
  },
  {
    "gender": "male",
    "total_spend": "336962.16",
    "total_transactions": 10451,
    "number_of_users": 6127,
    "average_transaction_value": "32.24",
    "average_transactions_per_user": 1.71
  }
]
```

## 4. ZAKLJUČAK

**Performanse:**  
Sa vremenom izvršavanja od skoro 7 sekundi, upit je izuzetno spor. Uzrok je COLLSCAN na celoj `transactions` kolekciji.

**Poslovni uvid:**  
Upit pruža izuzetno vrednu segmentaciju kupaca po polu. Iz rezultata se vidi da su oba pola veoma slična u svojim potrošačkim navikama. Muškarci u proseku obave neznatno više transakcija, ali im je prosečna vrednost transakcije nešto niža.

