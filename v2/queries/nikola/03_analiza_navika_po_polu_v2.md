# UPIT 3: Analiza potrošačkih navika po polu (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je optimizovan korišćenjem **sparse indeksa** za brzo filtriranje transakcija registrovanih korisnika i denormalizacijom podataka, čime je potpuno eliminisana potreba za `$lookup` operacijom.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Brzo filtriranje samo transakcija registrovanih korisnika pomoću sparse indeksa.
  {
    $match: {
      "user.id": { $ne: null }
    }
  },
  // FAZA 2: Grupisanje po polu. Svi podaci (pol, ID korisnika) su direktno dostupni.
  {
    $group: {
      _id: "$user.gender",
      totalSpend: { $sum: "$amounts.final" },
      totalTransactions: { $sum: 1 },
      totalUsers: { $addToSet: "$user.id" }
    }
  },
  // FAZA 3: Projekcija i izračunavanje finalnih metrika.
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
    $sort: { gender: 1 }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan:**

| Metrika                  | V1 Šema (Stari Upit)      | V2 Šema (Novi Upit)        | Promena                        |
|---------------------------|--------------------------|----------------------------|--------------------------------|
| Vreme izvršavanja         | 6,761 ms (~7 sec)       | 110 ms                     | ~98% brže                      |
| Strategija                | COLLSCAN + `$lookup`    | IXSCAN (sparse) + FETCH    | Najefikasniji pristup           |
| Pregledanih dokumenata    | 1,240,620               | 20,538                     | Smanjenje I/O za 98.3%         |

**Tumačenje:**  
Plan izvršenja je idealan. IXSCAN strategija sa `idx_user_id_sparse` indeksom je trenutno pronašla tačno 20,538 relevantnih transakcija, potpuno ignorišući 98.3% kolekcije.

## 3. REZULTAT UPITA

Rezultat je identičan onom dobijenom nad V1 šemom.

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

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 7 sekundi na samo 110 milisekundi je izvanredno ubrzanje. Kreiranje sparse indeksa na `user.id` bilo je ključno.

**Poslovni uvid:**  
Uvid o sličnim potrošačkim navikama polova ostaje isti. Zahvaljujući V2 šemi, do ove važne informacije se sada dolazi skoro trenutno.

