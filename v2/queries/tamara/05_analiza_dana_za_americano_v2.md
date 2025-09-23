# UPIT 5: Analiza najprofitabilnijih dana za proizvod "Americano" (V2 - Optimizovano)

---

## 1. KOD UPITA

*Zahvaljujući ugrađenom nizu `items` koji sadrži sve detalje o prodatim artiklima, upit je drastično pojednostavljen. Nema više potrebe za spajanjem sa tri različite kolekcije. Sve se rešava jednim efikasnim prolazom kroz `transactions` kolekciju.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Brzo filtriraj samo transakcije koje sadrže "Americano"
  {
    $match: { "items.name": "Americano" }
  },
  // FAZA 2: "Rasturi" niz stavki da bi se radilo sa pojedinačnim prodajama
  {
    $unwind: "$items"
  },
  // FAZA 3: Filtriraj ponovo da bi se izolovale samo "Americano" stavke
  {
    $match: { "items.name": "Americano" }
  },
  // FAZA 4: Formatiraj datum i izdvoj prihod po stavci
  {
    $project: {
      saleDate: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      subtotal: "$items.subtotal"
    }
  },
  // FAZA 5: Grupiši po datumu da bi se dobio ukupan dnevni prihod
  {
    $group: {
      _id: "$saleDate",
      dailyRevenue: { $sum: "$subtotal" }
    }
  },
  // FAZA 6: Sortiraj i ograniči na top 5
  { $sort: { dailyRevenue: -1 } },
  { $limit: 5 },
  // FAZA 7: Formatiraj finalni izlaz
  {
    $project: {
      _id: 0,
      date: "$_id",
      total_revenue_for_americano: { $round: ["$dailyRevenue", 2] }
    }
  }
])
```
## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan**

| Metrika                  | V1 Šema (Stari Upit)       | V2 Šema (Novi Upit)      | Promena                       |
|---------------------------|---------------------------|-------------------------|-------------------------------|
| Vreme izvršavanja         | 49,932 ms (~50 sec)       | 12,348 ms (~12 sec)     | ~75% brže                     |
| Strategija                | COLLSCAN + 2x $lookup     | COLLSCAN (bez $lookup)  | Značajno smanjenje posla      |
| Pregledanih Dokumenata    | ~5,273,450                | 1,240,620               | Smanjenje I/O za 76%          |

**Tumačenje:**  
Ključni dobitak dolazi iz potpune eliminacije `$lookup` operacija. Umesto spajanja tri kolekcije, upit sada radi samo sa jednom, smanjujući broj pročitanih dokumenata sa preko 5 miliona na 1.24 miliona.

## 3. REZULTAT UPITA

Rezultat je identičan onom dobijenom nad V1 šemom.

```json
[
  { "date": "2023-07-02", "total_revenue_for_americano": "72513.00" },
  { "date": "2024-01-09", "total_revenue_for_americano": "71974.00" },
  { "date": "2024-01-05", "total_revenue_for_americano": "71960.00" },
  { "date": "2024-01-15", "total_revenue_for_americano": "71743.00" },
  { "date": "2024-01-18", "total_revenue_for_americano": "71603.00" }
]
```

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 50 sekundi na 12 sekundi (ubrzanje od 75%). Ugrađivanjem `items` niza, eliminisani su `$lookup`-ovi, što je drastično pojednostavilo logiku i smanjilo opterećenje.

**Poslovni uvid:**  
Uvid o najuspešnijim danima za prodaju "Americana" ostaje isti, ali je sada dostupan 4 puta brže, čineći analizu znatno praktičnijom.

