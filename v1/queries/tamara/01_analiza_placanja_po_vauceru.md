# UPIT 1: Analiza dominantnih načina plaćanja po tipu vaučera

---

## 1. KOD UPITA

*Prikazuje najčešće korišćene načine plaćanja za transakcije sa vaučerima, grupisane po tipu popusta vaučera.*

```javascript
db.getCollection('transactions').aggregate([
  {
    $match: {
      voucher_id: { $ne: null } // Filtrira samo transakcije sa vaučerima
    }
  },
  {
    $lookup: {
      from: "vouchers",
      localField: "voucher_id",
      foreignField: "_id",
      as: "voucherDetails"
    }
  },
  {
    $unwind: "$voucherDetails"
  },
  {
    $lookup: {
      from: "payment_methods",
      localField: "payment_method_id",
      foreignField: "_id",
      as: "paymentDetails"
    }
  },
  {
    $unwind: "$paymentDetails"
  },
  {
    $group: {
      _id: {
        voucherType: "$voucherDetails.discount_type",
        paymentMethod: "$paymentDetails.method_name"
      },
      count: { $sum: 1 }
    }
  },
  {
    $sort: { "_id.voucherType": 1, count: -1 }
  },
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
  {
    $project: {
      _id: 0,
      voucher_discount_type: "$_id",
      top_payment_methods: { $slice: ["$mostUsedPaymentMethods", 3] } // Top 3
    }
  },
  {
    $sort: { voucher_discount_type: 1 }
  }
])
```

## 2. ANALIZA PERFORMANSI (EXPLAIN PLAN)
- **Vreme izvršavanja (executionTimeMillis):** 8368 ms  
- **Ukupno pregledanih dokumenata (totalDocsExamined):** 1,240,620  
- **Ukupno pregledanih ključeva indeksa (totalKeysExamined):** 84,508  
- **Strategija izvršavanja:** `COLLSCAN` na **transactions** kolekciji praćen sa dva `$lookup`-a.

---

## 3. REZULTAT UPITA
```json
[
  {
    "voucher_discount_type": "percentage",
    "top_payment_methods": [
      { "method": "grabpay",     "count": 8582 },
      { "method": "tng",         "count": 8563 },
      { "method": "credit_card", "count": 8404 }
    ]
  }
]
```

## 4. ZAKLJUČAK

### Performanse
Upit se izvršavao nešto više od **8 sekundi**.  
Glavni uzrok sporosti je **COLLSCAN** koji skenira preko **1.2 miliona dokumenata**  
da bi pronašao oko **42 hiljade transakcija sa vaučerom**.  
Performanse bi se značajno poboljšale kreiranjem **indeksa na polju `voucher_id`**.

### Poslovni uvid
Za vaučere sa procentualnim popustom, **digitalni novčanici** (`grabpay`, `tng`)  
i **kreditne kartice** su podjednako popularni.  
Ovo ukazuje da korisnici vaučera rado koriste različite **digitalne metode plaćanja**  
i pokazuju visok nivo **tehnološke pismenosti**.



