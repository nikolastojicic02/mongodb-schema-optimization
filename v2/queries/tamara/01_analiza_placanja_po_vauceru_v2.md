# UPIT 1: Analiza dominantnih načina plaćanja po tipu vaučera (V2 - Optimizovano)

---

## 1. KOD UPITA

*Zahvaljujući V2 šemi, upit je sada mnogo jednostavniji. Nema potrebe za spajanjem (`$lookup`) sa `vouchers` i `payment_methods` kolekcijama, jer su svi potrebni podaci već ugrađeni. Korišćenje **sparse indeksa** dodatno ubrzava početno filtriranje.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Filtriraj samo transakcije sa vaučerima.
  // Ova faza je IZUZETNO BRZA zahvaljujući sparse indeksu na "voucher.id".
  {
    $match: {
      "voucher": { $ne: null }
    }
  },
  // FAZA 2: Grupiši po tipu vaučera i načinu plaćanja.
  // Podaci se čitaju direktno iz ugrađenih objekata, NEMA `$lookup`-a.
  {
    $group: {
      _id: {
        voucherType: "$voucher.discount_type",
        paymentMethod: "$payment_method.name"
      },
      count: { $sum: 1 }
    }
  },
  // FAZA 3: Sortiraj da bi se pripremilo za pronalaženje top 3.
  {
    $sort: { "_id.voucherType": 1, count: -1 }
  },
  // FAZA 4: Grupiši ponovo, samo po tipu vaučera, da se kreira niz metoda plaćanja.
  {
    $group: {
      _id: "$_id.voucherType",
      mostUsedPaymentMethods: {
        $push: {
          method: "$_id.paymentMethod",
          count: "$count"
        }
      }
    }
  },
  // FAZA 5: Finalna projekcija koja uzima samo prva 3 elementa iz niza.
  {
    $project: {
      _id: 0,
      voucher_discount_type: "$_id",
      top_payment_methods: { $slice: ["$mostUsedPaymentMethods", 3] }
    }
  },
  {
    $sort: { voucher_discount_type: 1 }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan**

| Metrika                    | V1 Šema (Stari Upit)   | V2 Šema (Novi Upit) | Promena                     |
|-----------------------------|----------------------|-------------------|----------------------------|
| Vreme izvršavanja           | 8368 ms (~8 sec)     | < 300 ms          | ~96% brže                 |
| Strategija                  | COLLSCAN + 2x $lookup| IXSCAN (sparse)   | Značajno smanjenje posla  |
| Pregledanih Dokumenata      | 1,240,620 (u startu) | ~42,253           | Drastično smanjenje I/O   |

**Tumačenje:** `winningPlan` koristi IXSCAN sa indeksom `idx_voucher_id_sparse`, što znači da baza trenutno pronalazi samo ~42,000 transakcija sa vaučerima. Dva skupa $lookup spajanja su potpuno eliminisana.

## 3. REZULTAT UPITA

Rezultat upita je potpuno identičan onom dobijenom nad V1 šemom.

```json
[
  {
    "voucher_discount_type": "percentage",
    "top_payment_methods": [
      { "method": "grabpay", "count": 8582 },
      { "method": "tng", "count": 8563 },
      { "method": "credit_card", "count": 8404 }
    ]
  }
]
```
## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa preko 8 sekundi na delić sekunde predstavlja poboljšanje od preko 96%. Kreiranjem sparse indeksa na `voucher.id` eliminisan je COLLSCAN. Denormalizacijom je eliminisana potreba za `$lookup` operacijama.

**Poslovni uvid:**  
Uvid o dominantnim načinima plaćanja kod korisnika vaučera ostaje isti, ali je sada dostupan skoro trenutno, što omogućava mnogo brže cikluse analize.

