# UPIT 4: Demografska analiza potrošnje po polu i starosnim grupama

---

## 1. KOD UPITA

*Segmentira transakcije po polu i starosnim grupama korisnika, a zatim izračunava prosečnu vrednost transakcije i ukupan broj transakcija za svaki segment.*

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
    $project: {
      _id: 0,
      gender: "$userDetails.gender",
      final_amount: "$amounts.final",
      birthYear: { $year: "$userDetails.birthdate" }
    }
  },
  {
    $addFields: {
      age: { $subtract: [2024, "$birthYear"] }
    }
  },
  {
    $project: {
      gender: 1,
      final_amount: 1,
      ageGroup: {
        $switch: {
          branches: [
            { case: { $lt: ["$age", 25] }, then: "1) < 25" },
            { case: { $and: [{ $gte: ["$age", 25] }, { $lt: ["$age", 35] }] }, then: "2) 25-34" },
            { case: { $and: [{ $gte: ["$age", 35] }, { $lt: ["$age", 45] }] }, then: "3) 35-44" },
            { case: { $gte: ["$age", 45] }, then: "4) 45+" }
          ],
          default: "Nepoznato"
        }
      }
    }
  },
  {
    $group: {
      _id: {
        gender: "$gender",
        ageGroup: "$ageGroup"
      },
      averageTransactionValue: { $avg: "$final_amount" },
      transactionCount: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      gender: "$_id.gender",
      age_group: "$_id.ageGroup",
      average_transaction_value: { $round: ["$averageTransactionValue", 2] },
      transaction_count: "$transactionCount"
    }
  },
  {
    $sort: {
      gender: 1,
      age_group: 1
    }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja (executionTimeMillis):** 8,934 ms  
- **Ukupno pregledanih dokumenata (totalDocsExamined):** 1,240,620  
- **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** 0  
- **Strategija izvršavanja:** COLLSCAN na `transactions` kolekciji.

## 3. REZULTAT UPITA

```json
[
  { "gender": "female", "age_group": "1) < 25", "average_transaction_value": "33.31", "transaction_count": 2147 },
  { "gender": "female", "age_group": "2) 25-34", "average_transaction_value": "32.91", "transaction_count": 2241 },
  { "gender": "female", "age_group": "3) 35-44", "average_transaction_value": "33.75", "transaction_count": 2182 },
  { "gender": "female", "age_group": "4) 45+", "average_transaction_value": "33.02", "transaction_count": 3517 },
  { "gender": "male", "age_group": "1) < 25", "average_transaction_value": "32.91", "transaction_count": 2209 },
  { "gender": "male", "age_group": "2) 25-34", "average_transaction_value": "33.04", "transaction_count": 2258 },
  { "gender": "male", "age_group": "3) 35-44", "average_transaction_value": "33.30", "transaction_count": 2334 },
  { "gender": "male", "age_group": "4) 45+", "average_transaction_value": "33.04", "transaction_count": 3650 }
]
```

## 4. ZAKLJUČAK

**Performanse:**  
Vreme izvršavanja od skoro 9 sekundi je neprihvatljivo. Problem je, kao i u prethodnim slučajevima, nedostatak indeksa na `user_id` polju, što dovodi do neefikasnog COLLSCAN-a.

**Poslovni uvid:**  
Prosečna vrednost transakcije je izuzetno stabilna (oko 33) u svim demografskim segmentima. Starosna grupa "45+" je ubedljivo najaktivnija, sa značajno većim brojem transakcija od svih mlađih grupa za oba pola, što ih čini najvrednijim segmentom kupaca.
