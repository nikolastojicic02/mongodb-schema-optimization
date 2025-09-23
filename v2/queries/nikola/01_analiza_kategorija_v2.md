# UPIT 1: Analiza performansi po kategorijama (V2 - Optimizovano)

---

## 1. KOD UPITA

*Zahvaljujući ugrađivanju svih stavki transakcije u V2 šemu, više nema potrebe za radom sa `transaction_items` kolekcijom niti za spajanjem sa `menu_items` kolekcijom. Upit se izvršava nad jednom `transactions` kolekcijom, značajno je jednostavniji i neuporedivo brži.*

```javascript
db.transactions.aggregate([
  // FAZA 1: "Rasturi" (unwind) niz ugrađenih stavki 'items'.
  {
    $unwind: "$items"
  },
  // FAZA 2: Grupiši po kategoriji koja je sada direktno dostupna unutar svake stavke.
  {
    $group: {
      _id: "$items.category",
      totalRevenue: { $sum: "$items.subtotal" },
      totalQuantitySold: { $sum: "$items.quantity" }
    }
  },
  // FAZA 3: Sortiraj rezultate po ukupnom prihodu.
  {
    $sort: {
      totalRevenue: -1
    }
  },
  // FAZA 4: Finalna projekcija i izračunavanje prosečne cene.
  {
    $project: {
      _id: 0,
      category: "$_id",
      total_revenue: { $round: ["$totalRevenue", 2] },
      total_items_sold: "$totalQuantitySold",
      average_price_per_item: {
        $round: [
          { $divide: ["$totalRevenue", "$totalQuantitySold"] },
          2
        ]
      }
    }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan:**

| Metrika                  | V1 Šema (Stari Upit)     | V2 Šema (Novi Upit)     | Promena                         |
|---------------------------|-------------------------|-------------------------|---------------------------------|
| Vreme izvršavanja         | 236,508 ms (~4 min)     | 8,829 ms (~9 sec)       | ~96% brže                       |
| Strategija                | COLLSCAN + `$lookup`    | COLLSCAN + `$unwind`    | Eliminisan najskuplji deo       |
| Pregledanih dokumenata    | 2,481,642               | 1,240,620               | Smanjeno za 50%                 |

**Tumačenje:**  
Ključna razlika je odsustvo `$lookup` faze. Umesto da za 2.5 miliona stavki radi 2.5 miliona pojedinačnih operacija spajanja sa drugom kolekcijom (što je izuzetno skupo), novi upit sve potrebne podatke dobija jednim, kontinualnim čitanjem sa diska.

## 3. REZULTAT UPITA

Rezultat upita je potpuno identičan onom dobijenom nad V1 šemom.

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

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 4 minuta na manje od 9 sekundi predstavlja ubrzanje od preko 96%, pretvarajući neizvodljiv upit u praktičan analitički alat. Ugrađivanjem niza `items` direktno u svaku transakciju, potpuno je eliminisan `$lookup` i potreba za `transaction_items` kolekcijom.

**Poslovni uvid:**  
Uvid da je kafa glavni pokretač prihoda ostaje isti. Međutim, sa V2 šemom, ovaj uvid je dostupan za nekoliko sekundi, a ne minuta, što omogućava donošenje odluka skoro u realnom vremenu.

