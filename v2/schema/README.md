# Šema baze podataka - Verzija V2 (optimizovana šema)

Ovaj dokument opisuje strukturu baze podataka `coffee_db_v2`. Za razliku od V1, ova šema je **denormalizovana** i optimizovana za brze analitičke upite. Cilj je da se izbegnu skupe `$lookup` (JOIN) operacije tako što se svi relevantni podaci za jednu transakciju smeštaju u **jedan jedini dokument**.

## Glavna kolekcija

U ovoj verziji, gotovo svi podaci su smešteni u jednu kolekciju:

1.  **`transactions`** - Svaki dokument predstavlja jednu kompletnu transakciju sa svim ugnježdenim (embedovanim) podacima.

---

## Detaljan prikaz dokumenta u kolekciji `transactions`

Sledeći primer prikazuje strukturu jednog dokumenta. Mnogi podaci koji su u V1 šemi bili samo reference (ID-jevi), ovde su ugnježdeni kao pod-dokumenti.

```json
{
  "_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // String (UUID)
  "created_at": "2023-07-15T14:45:10.000Z", // BSON DateTime
  "amounts": {
    "original": "15.75", // BSON Decimal128
    "discount": "1.57",  // BSON Decimal128
    "final": "14.18"     // BSON Decimal128
  },

  // --- Primenjeni Dizajn Šabloni ---

  // 1. Šablon Proračunavanja (Computed Pattern)
  "createdAtDetails": {
    "year": 2023,       // Integer
    "month": 7,         // Integer
    "dayOfWeek": 6,     // Integer (1=Ponedeljak, 7=Nedelja)
    "hour": 14          // Integer
  },

  // 2. Šablon Proširene Reference (Extended Reference Pattern)
  "store": {
    "id": 1,
    "name": "Coffee Corner Downtown",
    "city": "Metropolis"
  },
  "payment_method": {
    "id": 1,
    "name": "Credit Card"
  },
  "user": { // Može biti null ako korisnik nije registrovan
    "id": 123,
    "gender": "Female",
    "birthdate": "1990-05-15T00:00:00.000Z", // BSON DateTime
    "age_group": "2) 25-34" // Proračunato polje
  },
  "voucher": { // Može biti null ako vaučer nije korišćen
    "id": 5,
    "discount_type": "percentage"
  },

  // 3. Šablon Ugrađivanja (Embedding Pattern)
  "items": [ // Niz ugnježdenih dokumenata
    {
      "menu_item_id": 101,
      "name": "Espresso",
      "category": "Coffee",
      "quantity": 2,
      "unit_price": "2.50", // BSON Decimal128
      "subtotal": "5.00"   // BSON Decimal128
    },
    {
      "menu_item_id": 205,
      "name": "Croissant",
      "category": "Pastry",
      "quantity": 1,
      "unit_price": "3.00", // BSON Decimal128
      "subtotal": "3.00"   // BSON Decimal128
    }
  ],
  "item_count": 2 // Proračunato polje za lakše filtriranje
}
```

## Primenjeni MongoDB dizajn šabloni

Ova šema aktivno koristi nekoliko preporučenih MongoDB dizajn šablona za postizanje boljih performansi:

1.  **Ugrađivanje podataka (Embedding):** Umesto posebne `transaction_items` kolekcije, sve stavke transakcije su sada niz (`items`) unutar glavnog dokumenta. Ovo omogućava dobavljanje svih podataka o transakciji u jednom čitanju sa diska.

2.  **Proširena referenca (Extended Reference):** Umesto da čuvamo samo `store_id` ili `user_id`, mi čuvamo i najčešće potrebne podatke uz ID (npr. `store.name`, `user.gender`). Ovo eliminiše potrebu za `$lookup` operacijama u većini upita.

3.  **Proračunavanje (Computed Pattern):** Polja koja se često koriste za filtriranje ili grupisanje, a koja se mogu izračunati prilikom upisa, čuvaju se direktno u dokumentu. Primeri su `createdAtDetails` (za analizu po danu, satu...), `user.age_group` i `item_count`. Ovo drastično ubrzava agregacije.