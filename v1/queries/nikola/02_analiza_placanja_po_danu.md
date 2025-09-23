# UPIT 2: Analiza promene načina plaćanja tokom dana

---

## 1. KOD UPITA

*Ovaj upit analizira procenat korišćenja gotovine (cash) u jutarnjim i popodnevnim satima.*

```javascript
db.getCollection('transactions').aggregate([
  // FAZA 1: Spoji SVE transakcije sa detaljima o načinu plaćanja
  {
    $lookup: {
      from: "payment_methods",
      localField: "payment_method_id",
      foreignField: "_id",
      as: "paymentDetails"
    }
  },
  { $unwind: "$paymentDetails" },

  // FAZA 2: Za svaku transakciju, odredi period dana i da li je plaćena gotovinom
  {
    $project: {
      period: {
        $cond: [{ $lt: [{ $hour: "$created_at" }, 12] }, "Morning (AM)", "Afternoon (PM)"]
      },
      isCash: { $eq: ["$paymentDetails.method_name", "cash"] }
    }
  },

  // FAZA 3: Grupiši po periodu i prebroj ukupne i gotovinske transakcije
  {
    $group: {
      _id: "$period",
      totalTransactions: { $sum: 1 },
      cashTransactions: { $sum: { $cond: ["$isCash", 1, 0] } }
    }
  },

  // FAZA 4: Izračunaj procenat
  {
    $project: {
      _id: 0,
      period: "$_id",
      cash_usage_percentage: {
        $round: [{ $multiply: [{ $divide: ["$cashTransactions", "$totalTransactions"] }, 100] }, 2]
      }
    }
  }
])
```


## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja:** 94,126 ms (~94 sekunde)  
- **Strategija:** COLLSCAN + `$lookup`  
- **Pregledanih dokumenata:** 1,240,620 (`transactions`) + 1,240,621 (`payment_methods`)  
- **Pregledanih ključeva:** 1,240,621 (korišćen `_id` indeks na `payment_methods` tokom `$lookup`-a)  
- **Tumačenje:** COLLSCAN na početku čita svih 1.24 miliona transakcija. Glavno usko grlo je `$lookup` faza koja se izvršava 1.24 miliona puta.

## 3. REZULTAT UPITA

```json
[
  { "period": "Afternoon (PM)", "cash_usage_percentage": 19.91 },
  { "period": "Morning (AM)", "cash_usage_percentage": 20.07 }
]
```
## 4. ZAKLJUČAK

**Performanse:**  
Upit je katastrofalno spor. Vreme izvršavanja od preko 90 sekundi je direktna posledica COLLSCAN strategije praćene masivnim `$lookup`-om. V1 šema je potpuno neprikladna za ovaj tip analize.

**Poslovni uvid:**  
Uvid da je udeo gotovine stabilan tokom celog dana je koristan, ali je cena dobijanja tog uvida previsoka. Čekanje od minut i po na odgovor čini bilo kakvu agilnu analizu ili korišćenje u realnom vremenu nemogućim.
