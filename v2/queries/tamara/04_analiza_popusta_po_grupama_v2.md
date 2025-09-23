# UPIT 4: Analiza prosečnog popusta po starosnoj grupi (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je drastično pojednostavljen. Nema više potrebe za spajanjem sa `users` kolekcijom niti za izračunavanjem starosti "u letu". Svi potrebni podaci (postojanje vaučera, starosna grupa korisnika) su direktno dostupni u `transactions` dokumentu.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Filtriraj transakcije koje imaju vaučer I definisanu starosnu grupu
  {
    $match: {
      voucher: { $ne: null },
      "user.age_group": { $ne: null }
    }
  },
  // FAZA 2: Grupiši po pre-kalkulisanoj starosnoj grupi i izračunaj prosek popusta
  {
    $group: {
      _id: "$user.age_group",
      averageDiscount: { $avg: "$amounts.discount" }
    }
  },
  // FAZA 3: Formatiraj finalni izlaz
  {
    $project: {
      _id: 0,
      age_group: "$_id",
      average_discount_applied: { $round: ["$averageDiscount", 2] }
    }
  },
  { $sort: { age_group: 1 } }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan**

| Metrika                  | V1 Šema (Stari Upit)         | V2 Šema (Novi Upit)               | Promena                       |
|---------------------------|-----------------------------|----------------------------------|-------------------------------|
| Vreme izvršavanja         | 10,919 ms (~11 sec)        | 3,965 ms (~4 sec)               | ~64% brže                     |
| Strategija                | COLLSCAN + $lookup + Izračunavanje | COLLSCAN (ali bez $lookup-a i računanja) | Značajno smanjenje posla      |
| Pregledanih Dokumenata    | 1,240,620                   | 1,240,620                        | Isto                           |

**Tumačenje:**  
Iako strategija ostaje COLLSCAN (jer nema složenog indeksa koji pokriva oba uslova), ključno poboljšanje dolazi iz eliminacije `$lookup`-a i izračunavanja "u letu". Ukupan rad koji baza mora da obavi je drastično manji.

## 3. REZULTAT UPITA

Rezultat upita je identičan onom dobijenom nad V1 šemom.

```json
[
  { "age_group": "1) < 25", "average_discount_applied": "2.05" },
  { "age_group": "2) 25-34", "average_discount_applied": "2.29" },
  { "age_group": "3) 35-44", "average_discount_applied": "2.33" },
  { "age_group": "4) 45+", "average_discount_applied": "2.33" }
]
```

## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa skoro 11 sekundi na ispod 4 sekunde (ubrzanje od 64%). Ugrađivanjem podataka o korisniku i pre-kalkulisane starosne grupe, potpuno su eliminisani `$lookup` i faze za izračunavanje.

**Poslovni uvid:**  
Uvid o prosečnom popustu po starosnim grupama ostaje isti, ali je sada dostupan skoro tri puta brže, što analizu čini znatno praktičnijom.

