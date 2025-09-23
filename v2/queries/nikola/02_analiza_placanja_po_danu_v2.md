# UPIT 2: Analiza promene načina plaćanja tokom dana (V2 - Optimizovano)

---

## 1. KOD UPITA

*Zahvaljujući V2 šemi, upit je značajno pojednostavljen i ubrzan. Koristi pre-kalkulisano polje `createdAtDetails.hour` i ugrađeno polje `payment_method.name`, čime se eliminišu i izračunavanje "u letu" i najskuplja operacija - `$lookup`.*

```javascript
db.transactions.aggregate([
  {
    $project: {
      period: {
        $cond: {
          if: { $lt: ["$createdAtDetails.hour", 12] },
          then: "Morning (AM)",
          else: "Afternoon (PM)"
        }
      },
      isCash: { $eq: ["$payment_method.name", "cash"] }
    }
  },
  {
    $group: {
      _id: "$period",
      totalTransactions: { $sum: 1 },
      cashTransactions: { $sum: { $cond: { if: "$isCash", then: 1, else: 0 } } }
    }
  },
  {
    $project: {
      _id: 0,
      period: "$_id",
      cash_usage_percentage: {
        $round: [
          { $multiply: [{ $divide: ["$cashTransactions", "$totalTransactions"] }, 100] },
          2
        ]
      }
    }
  },
  {
    $sort: { period: 1 }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan:**

| Metrika                  | V1 Šema (Stari Upit)      | V2 Šema (Novi Upit)      | Promena                        |
|---------------------------|--------------------------|--------------------------|--------------------------------|
| Vreme izvršavanja         | 94,126 ms (~94 sec)      | 1,963 ms (~2 sec)       | ~98% brže                      |
| Strategija                | COLLSCAN + `$lookup`     | COLLSCAN                | Ogromno smanjenje posla        |
| Pregledanih dokumenata    | ~2,481,241               | 1,240,620               | Smanjenje I/O za 50%           |

**Tumačenje:**  
Najvažnija optimizacija je potpuna eliminacija `$lookup` faze. Umesto da za 1.24 miliona transakcija radi 1.24 miliona spajanja sa drugom kolekcijom, V2 upit sve potrebne podatke pronalazi direktno u dokumentu koji čita.

## 3. REZULTAT UPITA

Rezultati su identični onima dobijenim nad V1 šemom.

```json
[
  { "period": "Afternoon (PM)", "cash_usage_percentage": 19.91 },
  { "period": "Morning (AM)", "cash_usage_percentage": 20.07 }
]
```

### 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Optimizacija V2 šeme je imala dramatičan efekat. Smanjenje vremena izvršavanja sa 94 sekunde na manje od 2 sekunde predstavlja ubrzanje od oko 98%. Rešenje je bila denormalizacija (ugrađivanje imena načina plaćanja) i korišćenje pre-kalkulisanog polja za sat.

**Poslovni uvid:**  
Uvid da je udeo gotovine stabilan tokom celog dana ostaje isti. Zahvaljujući V2 šemi, do ovog uvida se sada dolazi skoro 50 puta brže.

