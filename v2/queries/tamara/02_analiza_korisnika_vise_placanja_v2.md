# UPIT 2: Analiza korisnika sa više metoda plaćanja (V2 - Optimizovano)

---

## 1. KOD UPITA

*Upit je optimizovan korišćenjem **sparse indeksa** za brzo pronalaženje transakcija registrovanih korisnika i denormalizacijom podataka, čime je eliminisana potreba za `$lookup` operacijom.*

```javascript
db.transactions.aggregate([
  // FAZA 1: Filtriranje samo transakcija registrovanih korisnika korišćenjem sparse indeksa.
  {
    $match: {
      "user.id": { $ne: null }
    }
  },
  // FAZA 2: Grupisanje po korisniku, prikupljanje podataka iz ugrađenih objekata.
  {
    $group: {
      _id: "$user.id",
      user_gender: { $first: "$user.gender" },
      uniquePaymentMethods: { $addToSet: "$payment_method.id" },
      totalTransactions: { $sum: 1 },
      totalSpend: { $sum: "$amounts.final" }
    }
  },
  // FAZA 3: Filtriranje korisnika sa 2 ili više metoda plaćanja.
  {
    $match: {
      $expr: { $gte: [{ $size: "$uniquePaymentMethods" }, 2] }
    }
  },
  // FAZA 4: Projekcija i formatiranje rezultata.
  {
    $project: {
      _id: 0,
      user_id: "$_id",
      user_gender: 1,
      number_of_payment_methods: { $size: "$uniquePaymentMethods" },
      average_transaction_value: { $round: [{ $divide: ["$totalSpend", "$totalTransactions"] }, 2] },
      total_transactions: "$totalTransactions"
    }
  },
  // FAZA 5: Sortiranje.
  {
    $sort: {
      number_of_payment_methods: -1,
      average_transaction_value: -1
    }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)

**Uporedni explain plan**

| Metrika                    | V1 Šema (Stari Upit) | V2 Šema (Novi Upit) | Promena                    |
|-----------------------------|---------------------|--------------------|----------------------------|
| Vreme izvršavanja           | 3093 ms (~3 sec)    | 418 ms             | ~86% brže                 |
| Strategija                  | COLLSCAN + $lookup  | IXSCAN (sparse) + FETCH | Najefikasniji pristup |
| Pregledanih Dokumenata      | 1,240,620           | 20,538             | Smanjenje I/O za 98.3%    |

**Tumačenje:**  
IXSCAN strategija sa `idx_user_id_sparse` indeksom direktno pristupa samo relevantnim transakcijama. Odsustvo `$lookup` faze znači da se ostatak operacija izvršava brzo u memoriji.

## 3. REZULTAT UPITA

Rezultat upita je identičan originalnom.

```json
[
  {
    "user_id": 8,
    "user_gender": "female",
    "number_of_payment_methods": 5,
    "average_transaction_value": "47.36",
    "total_transactions": 7
  },
  {
    "user_id": 148,
    "user_gender": "male",
    "number_of_payment_methods": 5,
    "average_transaction_value": "44.64",
    "total_transactions": 6
  }
]
```
## 4. UPOREDNI ZAKLJUČAK (V1 vs V2)

**Performanse:**  
Smanjenje vremena izvršavanja sa preko 3 sekunde na manje od pola sekunde predstavlja ubrzanje od 86%. Sparse indeks je omogućio bazi da ignoriše 98.3% kolekcije, a denormalizacija je eliminisala `$lookup`.

**Poslovni uvid:**  
"Napredni" korisnici se sada mogu identifikovati skoro trenutno, što omogućava mnogo brže i efikasnije sprovođenje ciljanih marketinških kampanja.

