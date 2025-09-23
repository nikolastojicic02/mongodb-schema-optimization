# UPIT 5: Analiza najprofitabilnijih dana za proizvod "Americano" (V1 Šema)

---

## 1. KOD UPITA

*Ovaj upit pronalazi 5 dana sa najvećim prihodom od prodaje proizvoda "Americano". Zahteva dva uzastopna `$lookup`-a (spajanja) da bi povezao artikle sa datumima transakcija.*

```javascript
db.getCollection('menu_items').aggregate([
  // FAZA 1: Pronađi ID za proizvod "Americano"
  { $match: { name: "Americano" } },

  // FAZA 2: Spoji sa svim stavkama transakcija koje odgovaraju tom ID-u
  {
    $lookup: {
      from: "transaction_items",
      localField: "_id",
      foreignField: "menu_item_id",
      as: "sales"
    }
  },
  { $unwind: "$sales" },

  // FAZA 3: Spoji sa transakcijama da bi se dobio datum
  {
    $lookup: {
      from: "transactions",
      localField: "sales.transaction_id",
      foreignField: "_id",
      as: "transactionDetails"
    }
  },
  { $unwind: "$transactionDetails" },

  // FAZA 4: Formatiraj datum i izdvoj prihod po stavci
  {
    $project: {
      saleDate: { $dateToString: { format: "%Y-%m-%d", date: "$transactionDetails.created_at" } },
      subtotal: "$sales.subtotal"
    }
  },

  // FAZA 5: Grupiši po datumu da bi se dobio ukupan dnevni prihod
  {
    $group: {
      _id: "$saleDate",
      dailyRevenue: { $sum: "$subtotal" }
    }
  },

  // FAZA 6: Sortiraj i ograniči na top 5 dana
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

**Vreme izvršavanja:** 49,932 ms (~50 sec)  
**Strategija:** COLLSCAN + 2x $lookup  
**Pregledanih dokumenata:** ~5,273,450 (ogroman broj)  
**Pregledanih ključeva:** 310,166  

**Tumačenje:**  
Performanse su katastrofalne. Najveći problem je prvi **$lookup** koji mora da izvrši **COLLSCAN** nad celom `transaction_items` kolekcijom (~2.5 miliona dokumenata).

---

## 3. REZULTAT UPITA

Rezultat prikazuje 5 dana sa najvećim prihodom od prodaje **Americano**:

```json
[
  { "date": "2023-07-02", "total_revenue_for_americano": "72513.00" },
  { "date": "2024-01-09", "total_revenue_for_americano": "71974.00" },
  { "date": "2024-01-05", "total_revenue_for_americano": "71960.00" },
  { "date": "2024-01-15", "total_revenue_for_americano": "71743.00" },
  { "date": "2024-01-18", "total_revenue_for_americano": "71603.00" }
]
```
## 4. ZAKLJUČAK

### Performanse
Upit je praktično neupotrebljiv za agilnu analizu.  
Vreme izvršavanja od skoro **50 sekundi** je direktna posledica **normalizovane šeme** koja zahteva višestruka spajanja ($lookup) nad velikim kolekcijama.  
Najveći problem je prvi **$lookup** koji mora da izvrši **COLLSCAN** nad celom `transaction_items` kolekcijom (~2.5 miliona dokumenata).

### Poslovni uvid
Uvid o **najuspešnijim danima** za prodaju ključnog proizvoda (*Americano*) je vredan,  
ali je zbog loših performansi dobijanje tog uvida **presporo** za potrebe poslovnog odlučivanja.

