# UPIT 3: Analiza "Vikend Gužve" po satima (V1 Šema)

---

## 1. KOD UPITA

*Ovaj upit analizira ukupan prihod za svaki sat tokom vikenda (subota i nedelja). Napomena: U MongoDB, `$dayOfWeek` vraća 1 za Nedelju, a 7 za Subotu.*

```javascript
db.getCollection('transactions').aggregate([
  // FAZA 1: Za svaki dokument, izračunaj dan u nedelji i sat.
  {
    $project: {
      dayOfWeek: { $dayOfWeek: "$created_at" },
      hourOfDay: { $hour: "$created_at" },
      finalAmount: "$amounts.final"
    }
  },
  // FAZA 2: Filtriraj i zadrži samo one koji su se desili subotom ili nedeljom.
  {
    $match: {
        dayOfWeek: { $in: [1, 7] }
    }
  },
  // FAZA 3: Grupiši po satu i sumiraj prihod.
  {
    $group: {
      _id: "$hourOfDay",
      totalRevenue: { $sum: "$finalAmount" }
    }
  },
  // FAZA 4: Sortiraj po satu.
  {
   dayOfWeek: { $in: [1, 7] }
  },
  // FAZA 5: Formatiraj izlaz.
  {
    $project: {
      _id: 0,
      hour: "$_id",
      total_revenue: { $round: ["$totalRevenue", 2] }
    }
  }
])
```
## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja:** `10973 ms` (~11 sec)  
- **Strategija:** `COLLSCAN + $project`  
- **Pregledanih dokumenata:** `1,240,620`  
- **Pregledanih ključeva:** `0`  

**Tumačenje:**  
Upit je **neefikasan** jer baza mora da izvrši **COLLSCAN** i pročita svaki od 1.24 miliona dokumenata da bi „u letu“ izračunala dan u nedelji i sat. Tek nakon toga se vrši filtriranje.

---

## 3. REZULTAT UPITA

Rezultati prikazuju jasan obrazac prometa tokom vikenda, sa vrhuncem oko podneva.

### JSON
```json
[
  { "hour": 7,  "total_revenue": "257820.64" },
  { "hour": 8,  "total_revenue": "536167.50" },
  { "hour": 9,  "total_revenue": "937770.96" },
  { "hour": 10, "total_revenue": "1397832.80" },
  { "hour": 11, "total_revenue": "1780487.46" },
  { "hour": 12, "total_revenue": "1929640.72" },
  { "hour": 13, "total_revenue": "1772212.58" },
  { "hour": 14, "total_revenue": "1398599.32" },
  { "hour": 15, "total_revenue": "945209.76" },
  { "hour": 16, "total_revenue": "535401.56" },
  { "hour": 17, "total_revenue": "258496.66" },
  { "hour": 18, "total_revenue": "108447.54" },
  { "hour": 19, "total_revenue": "36418.06"  }
]
```

## 4. ZAKLJUČAK

### Performanse
- Vreme izvršavanja od skoro **11 sekundi** je direktna posledica **COLLSCAN**-a i izračunavanja „u letu“ za **1.24 miliona dokumenata**.  
- Šema baze **nije prilagođena** ovakvom tipu analize.

### Poslovni uvid
- Promet tokom vikenda dostiže **vrhunac u 12 časova**, sa značajnom aktivnošću u periodu od **10h do 14h**.  
- Ovi podaci su ključni za **operativno planiranje** (*osoblje, zalihe*).
