# UPIT 5: Analiza najvrednijih transakcija (Jul 2023) (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je značajno pojednostavljen. Nema potrebe za spajanjem kolekcija (`$lookup`) jer su svi potrebni podaci (ime prodavnice, način plaćanja, kupljeni artikli) već ugrađeni u svaki dokument transakcije.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Brzo filtriranje po datumu
  {
    $match: {
      created_at: {
        $gte: ISODate("2023-07-01T00:00:00.000Z"),
        $lt: ISODate("2023-08-01T00:00:00.000Z")
      }
    }
  },
  // FAZA 2: Sortiranje po finalnoj vrednosti
  {
    $sort: {
      "amounts.final": -1
    }
  },
  // FAZA 3: Ograničavanje na prvih 5 rezultata
  {
    $limit: 5
  },
  // FAZA 4: Projekcija i formatiranje finalnog izlaza
  {
    $project: {
      _id: 1,
      final_amount: "$amounts.final",
      store_name: "$store.name",
      payment_method: "$payment_method.name",
      products_purchased: "$items.name"
    }
  }
])
```




---

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

### Uporedni `explain` plan
| Metrika | V1 Šema (Stari Upit) | V2 Šema (Novi Upit) | Promena |
|---|---|---|---|
| **Vreme izvršavanja** | `15418 ms` (~15 sec) | `2308 ms` (~2 sec) | **~85% brže** |
| **Strategija** | `COLLSCAN` + `SORT` + 4x `$lookup` | `IXSCAN` + `SORT` + `FETCH` | Fundamentalno poboljšanje |
| **Pregledanih Dokumenata**| `~1,240,630` (zbog lookup-a) | `5` | Drastično smanjenje I/O |

**Tumačenje:** Baza je iskoristila indeks `idx_date_finalAmount` da efikasno pronađe sve transakcije iz jula (`IXSCAN`), sortirala ih u memoriji i na kraju dohvatila samo 5 potrebnih dokumenata sa diska.

---

## 3. REZULTAT UPITA

*Rezultat upita je identičan onom dobijenom nad V1 šemom.*

```json
[
  {
    "_id": "69807d5d-0eaf-411d-ad7f-c786dc5c373b",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 89q",
    "payment_method": "debit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "d9430ed6-6862-4384-8500-ac2e394d8089",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 57W",
    "payment_method": "credit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "0e569659-fb7b-4c89-8233-9434ca9d4a28",
    "final_amount": "90.0",
    "store_name": "G Coffee @ USJ 57W",
    "payment_method": "cash",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "2346bcfd-520f-43ba-9599-43934670dfc3",
    "final_amount": "90.0",
    "store_name": "G Coffee @ Kondominium Putra",
    "payment_method": "grabpay",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  },
  {
    "_id": "e1a90e02-bd3d-4425-a551-3a8c6059c5f2",
    "final_amount": "90.0",
    "store_name": "G Coffee @ Alam Tun Hussein Onn",
    "payment_method": "credit_card",
    "products_purchased": [ "Matcha Latte", "Matcha Latte", "Matcha Latte" ]
  }
]
```


---

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:** Prelazak sa 15.4 sekunde na 2.3 sekunde predstavlja ubrzanje od oko 85%. Ugrađivanjem svih potrebnih podataka, potpuno smo eliminisali sva četiri `$lookup`-a, što je bio najveći dobitak, a korišćenje indeksa je izbeglo `COLLSCAN`.

**Poslovni uvid:** Uvid o popularnosti "Matcha Latte" u najvrednijim transakcijama ostaje isti, ali je sada dostupan značajno brže, omogućavajući efikasniju i agilniju analizu poslovanja.