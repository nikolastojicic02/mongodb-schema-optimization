# UPIT 3: Analiza "Vikend Gužve" po satima (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je optimizovan korišćenjem pre-kalkulisanog polja `createdAtDetails.dayOfWeek` i namenskog indeksa na tom polju. Ovim se izbegava skupa operacija izračunavanja "u letu" i omogućava bazi da odmah filtrira samo relevantne podatke.*

```javascript
// Napomena: Korišćeni su dani 6 (Subota) i 7 (Nedelja) jer Python-ov isoweekday()
// generiše te vrednosti, koje su sada sačuvane u bazi.
db.transactions.aggregate([
  // FAZA 1: Brzo filtriranje samo dana vikenda pomoću indeksa.
  {
    $match: {
      "createdAtDetails.dayOfWeek": { $in: }
    }
  },
  // FAZA 2: Grupisanje po pre-kalkulisanom satu i sumiranje prihoda.
  {
    $group: {
      _id: "$createdAtDetails.hour",
      totalRevenue: { $sum: "$amounts.final" }
    }
  },
  // FAZA 3: Sortiranje po satu.
  {
    $sort: { _id: 1 }
  },
  // FAZA 4: Formatiranje izlaza.
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

Uporedni explain plan:

| Metrika                  | V1 Šema (Stari Upit) | V2 Šema (Novi Upit) | Promena           |
|---------------------------|--------------------|--------------------|-----------------|
| Vreme izvršavanja         | 10,973 ms (~11 sec) | 1,521 ms (~1.5 sec) | ~86% brže       |
| Strategija                | COLLSCAN + $project | IXSCAN + FETCH      | Najefikasniji pristup |
| Pregledanih Dokumenata    | 1,240,620           | 359,733             | Smanjenje I/O za 71% |

**Tumačenje:**  
IXSCAN strategija sa indeksom `idx_dayOfWeek` direktno pristupa samo transakcijama od subote i nedelje. Ostatak od 71% kolekcije je potpuno ignorisan.

## 3. REZULTAT UPITA

Rezultat je identičan onom dobijenom nad V1 šemom.

```json
[
  { "hour": 7, "total_revenue": "257820.64" },
  { "hour": 8, "total_revenue": "536167.50" },
  { "hour": 9, "total_revenue": "937770.96" },
  { "hour": 10, "total_revenue": "1397832.80" },
  { "hour": 11, "total_revenue": "1780487.46" },
  { "hour": 12, "total_revenue": "1929640.72" },
  { "hour": 13, "total_revenue": "1772212.58" },
  { "hour": 14, "total_revenue": "1398599.32" },
  { "hour": 15, "total_revenue": "945209.76" },
  { "hour": 16, "total_revenue": "535401.56" },
  { "hour": 17, "total_revenue": "258496.66" },
  { "hour": 18, "total_revenue": "108447.54" },
  { "hour": 19, "total_revenue": "36418.06" }
]
```

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 11 sekundi na samo 1.5 sekundu (ubrzanje od 86%). Kreiranjem pre-kalkulisanog polja `createdAtDetails.dayOfWeek` i indeksa na njemu, omogućili smo bazi da izvrši efikasno "rano" filtriranje.

**Poslovni uvid:**  
Uvid o vrhuncu prometa vikendom ostaje isti, ali je sada dostupan 7 puta brže, što omogućava mnogo agilnije analize.

