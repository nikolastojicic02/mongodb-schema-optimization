# UPIT 4: Demografska analiza potrošnje po polu i starosnim grupama (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je drastično pojednostavljen i ubrzan. Koristi **sparse indeks** za efikasno filtriranje i direktno pristupa pre-kalkulisanim i ugrađenim podacima, eliminišući potrebu za spajanjem i kompleksnim izračunavanjima unutar upita.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Brzo filtriranje transakcija registrovanih korisnika pomoću sparse indeksa.
  {
    $match: {
      "user.id": { $ne: null }
    }
  },
  // FAZA 2: Direktno grupisanje po pre-kalkulisanim i ugrađenim podacima.
  {
    $group: {
      _id: {
        gender: "$user.gender",
        ageGroup: "$user.age_group"
      },
      averageTransactionValue: { $avg: "$amounts.final" },
      transactionCount: { $sum: 1 }
    }
  },
  // FAZA 3: Finalna projekcija.
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

**Uporedni explain plan:**

| Metrika                  | V1 Šema (Stari Upit)      | V2 Šema (Novi Upit)        | Promena                        |
|---------------------------|--------------------------|----------------------------|--------------------------------|
| Vreme izvršavanja         | 8,934 ms (~9 sec)       | 145 ms                     | ~98% brže                      |
| Strategija                | COLLSCAN + `$lookup`    | IXSCAN (sparse) + FETCH    | Najefikasniji pristup           |
| Pregledanih dokumenata    | 1,240,620               | 20,538                     | Smanjenje I/O za 98.3%         |

**Tumačenje:**  
IXSCAN je eliminisao COLLSCAN. Pre-kalkulisano polje `user.age_group` je eliminisalo potrebu za skupim izračunavanjima datuma unutar upita.

## 3. REZULTAT UPITA

Rezultat je identičan originalnom.

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

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 9 sekundi na samo 145 milisekundi je ubrzanje od preko 98%. Uspeh je rezultat kombinacije **sparse indeksa**, **denormalizacije** i **pre-kalkulisanih polja**.

**Poslovni uvid:**  
Uvid o dominantnoj "45+" starosnoj grupi ostaje isti, ali je sada dostupan skoro trenutno, omogućavajući brzu i efikasnu segmentaciju korisnika.


