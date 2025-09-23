# UPIT 1: Sveobuhvatna analiza performansi po kategorijama

---

## 1. KOD UPITA

*Za svaku kategoriju proizvoda izračunava ukupan prihod, ukupan broj prodatih artikala i prosečnu cenu po artiklu.*

```javascript
db.getCollection('transaction_items').aggregate([
  {
    $lookup: {
      from: "menu_items",
      localField: "menu_item_id",
      foreignField: "_id",
      as: "menu_item_details"
    }
  },
  {
    $unwind: {
      path: "$menu_item_details"
    }
  },
  {
    $group: {
      _id: "$menu_item_details.category",
      totalRevenue: {
        $sum: "$subtotal"
      },
      totalQuantitySold: {
        $sum: "$quantity"
      }
    }
  },
  {
    $sort: {
      totalRevenue: -1
    }
  },
  {
    $project: {
      _id: 0,
      category: "$_id",
      total_revenue: {
        $round: ["$totalRevenue", 2]
      },
      total_items_sold: "$totalQuantitySold",
      average_price_per_item: {
        $round: [
          {
            $divide: [
              "$totalRevenue",
              "$totalQuantitySold"
            ]
          },
          2
        ]
      }
    }
  }
], { allowDiskUse: true })
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

- **Vreme izvršavanja (executionTimeMillis):** 236,508 ms  
- **Ukupno pregledanih dokumenata (totalDocsExamined):** 2,481,642  
- **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** 2,481,643  
- **Strategija izvršavanja:** COLLSCAN na `transaction_items` praćen sa `$lookup` (koristeći IXSCAN na `menu_items`).

## 3. REZULTAT UPITA

```json
[
  {
    "category": "coffee",
    "total_revenue": "29474135.00",
    "total_items_sold": 3722974,
    "average_price_per_item": "7.92"
  },
  {
    "category": "non-coffee",
    "total_revenue": "11791679.00",
    "total_items_sold": 1241354,
    "average_price_per_item": "9.50"
  }
]
```

## 4. ZAKLJUČAK

**Performanse:**  
Upit se izvršavao izuzetno dugo, 236.5 sekundi (skoro 4 minuta). Plan izvršavanja jasno pokazuje i zašto: početna faza je morala da izvrši COLLSCAN, čitajući svaki od ~2.48 miliona dokumenata iz `transaction_items` kolekcije. Iako je `$lookup` faza koja sledi bila efikasna (koristila je indeks na `menu_items` kolekciji), ogromna količina početnih podataka i potreba da se svaki od njih spoji sa drugom kolekcijom predstavlja fundamentalno "usko grlo" ove referencirane šeme.

**Poslovni uvid:**  
Rezultati jasno pokazuju da je kategorija "coffee" apsolutni pokretač poslovanja, generišući više nego dvostruko veći prihod od "non-coffee" kategorije. Međutim, zanimljivo je da "non-coffee" proizvodi imaju značajno višu prosečnu cenu po artiklu (9.50 vs 7.92), što ukazuje da, iako se prodaju u manjim količinama, ovi proizvodi imaju višu maržu ili vrednost.
