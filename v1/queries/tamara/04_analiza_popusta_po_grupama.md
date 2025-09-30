# UPIT 4: Analiza prosečnog popusta po starosnoj grupi (V1 Šema)

---

## 1. KOD UPITA

*Ovaj upit izračunava prosečan iznos popusta za svaku starosnu grupu, ali samo za transakcije u kojima je korišćen vaučer.*

```javascript
db.getCollection('transactions').aggregate([
  // FAZA 1: Filtriraj transakcije koje imaju vaučer
  { $match: { voucher_id: { $ne: null } } },

  // FAZA 2: Spoji sa korisnicima da dobiješ datum rođenja
  {
    $lookup: {
      from: "users",
      localField: "user_id",
      foreignField: "_id",
      as: "userDetails"
    }
  },
  { $unwind: "$userDetails" },

  // FAZA 3: Izračunaj starost korisnika
  {
    $addFields: {
      age: { $subtract: [2025, { $year: "$userDetails.birthdate" }] }
    }
  },

  // FAZA 4: Odredi starosnu grupu na osnovu izračunate starosti
  {
    $addFields: {
      ageGroup: {
        $switch: {
          branches: [
            { case: { $lt: ["$age", 25] }, then: "1) < 25" },
            { case: { $and: [{ $gte: ["$age", 25] }, { $lt: ["$age", 35] }] }, then: "2) 25-34" },
            { case: { $and: [{ $gte: ["$age", 35] }, { $lt: ["$age", 45] }] }, then: "3) 35-44" },
            { case: { $gte: ["$age", 45] }, then: "4) 45+" }
          ],
          default: "Nepoznato"
        }
      }
    }
  },

  // FAZA 5: Grupiši po starosnoj grupi i izračunaj prosečan popust
  {
    $group: {
      _id: "$ageGroup",
      averageDiscount: { $avg: "$amounts.discount" }
    }
  },

  // FAZA 6: Formatiraj finalni izlaz
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

- **Vreme izvršavanja:** 10,919 ms (~11 sec)  
- **Strategija:** `COLLSCAN` + `$lookup` + Izračunavanje  
- **Pregledanih dokumenata:** 1,240,620  
- **Pregledanih ključeva:** 138 (samo za `$lookup`)  
- **Tumačenje:** Performanse su degradirane kombinacijom **COLLSCAN-a**, spajanja sa drugom kolekcijom (`$lookup`) i skupih izračunavanja „u letu“ za određivanje demografskog segmenta.

---

## 3. REZULTAT UPITA

Rezultati pokazuju da se prosečan iznos popusta blago povećava sa starosnom grupom korisnika.

```json
[
  { "age_group": "1) < 25", "average_discount_applied": "2.05" },
  { "age_group": "2) 25-34", "average_discount_applied": "2.29" },
  { "age_group": "3) 35-44", "average_discount_applied": "2.33" },
  { "age_group": "4) 45+",  "average_discount_applied": "2.33" }
]
```

## 4. ZAKLJUČAK

### Performanse
Upit je izrazito **neefikasan**, sa vremenom izvršavanja od skoro **11 sekundi**.  
Ovaj pristup je **neodrživ** za analitiku u realnom vremenu.

### Poslovni uvid
Stariji korisnici u proseku koriste vaučere sa nešto **većim popustom**.  
Ovaj uvid je interesantan za **targetiranje promotivnih kampanja**, ali je **cena dobijanja** takvog uvida previsoka i može da odloži donošenje odluka.

