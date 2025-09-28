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

  // --- Primenjeni dizajn šabloni ---

  // 1. Šablon proračunavanja (Computed Pattern)
  "createdAtDetails": {
    "year": 2023,       // Integer
    "month": 7,         // Integer
    "dayOfWeek": 6,     // Integer (1=Ponedeljak, 7=Nedelja)
    "hour": 14          // Integer
  },

  // 2. Šablon proširene reference (Extended Reference Pattern)
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

  // 3. Šablon ugrađivanja (Embedding Pattern)
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


## Strateški indeksi za V2 šemu

Da bi se u potpunosti iskoristile prednosti denormalizovane šeme, kreiran je set strateških indeksa. Svaki indeks je pažljivo odabran da drastično ubrza specifične vrste analitičkih upita, pretvarajući spore `COLLSCAN` (skeniranje cele kolekcije) operacije u munjevito brze `IXSCAN` (skeniranje indeksa) operacije.

---

### 1. Složeni indeks (`Compound Index`)

*   **Naziv indeksa:** `idx_date_finalAmount`
*   **Definicija:** `db.transactions.createIndex({ "created_at": 1, "amounts.final": -1 })`
*   **Zašto ova vrsta?** Složeni indeks optimizuje upite koji filtriraju po prvom polju (`created_at`) i sortiraju po drugom (`amounts.final`). Redosled polja u indeksu je ključan i prati redosled operacija u upitu.
*   **Šta omogućava?** Ovo je **ključni indeks** za upite tipa "Top N", kao što je "pronađi 5 najvrednijih transakcija u julu". Omogućava bazi da:
    1.  Trenutno pronađe početak opsega za jul koristeći `created_at`.
    2.  Čita podatke koji su **već sortirani** po `amounts.final`, eliminišući potrebu za skupim sortiranjem u memoriji.

---

### 2. Jednostavni indeksi (`Single-Field Indexes`)

*   **Nazivi indeksa:** `idx_store_id`, `idx_dayOfWeek`
*   **Definicije:**
    *   `db.transactions.createIndex({ "store.id": 1 })`
    *   `db.transactions.createIndex({ "createdAtDetails.dayOfWeek": 1 })`
*   **Zašto ova vrsta?** Ovo su osnovni indeksi koji ubrzavaju bilo kakvo filtriranje ili grupisanje po jednom polju.
*   **Šta omogućavaju?** Brze odgovore na pitanja poput:
    *   "Koliki je ukupan prihod za prodavnicu X?" (`idx_store_id`)
    *   "Uporedi promet ponedeljkom i petkom." (`idx_dayOfWeek`)

---

### 3. Proređeni indeksi (`Sparse Indexes`)

*   **Nazivi indeksa:** `idx_user_id_sparse`, `idx_voucher_id_sparse`
*   **Definicije:**
    *   `db.transactions.createIndex({ "user.id": 1 }, { sparse: true })`
    *   `db.transactions.createIndex({ "voucher.id": 1 }, { sparse: true })`
*   **Zašto ova vrsta?** Proređeni indeks uključuje unose **samo za dokumente koji sadrže indeksirano polje**. Pošto mnoge transakcije nemaju korisnika ili vaučer (`user` ili `voucher` polje je `null`), ovaj tip indeksa je **manji i efikasniji**.
*   **Šta omogućava?** Efikasnu analizu koja se odnosi isključivo na registrovane korisnike ili korišćene vaučere (npr. "pronađi sve transakcije korisnika Y"), ignorišući sve anonimne transakcije.

---

### 4. Višeključni indeks (`Multikey Index`)

*   **Naziv indeksa:** `idx_items_category_multikey`
*   **Definicija:** `db.transactions.createIndex({ "items.category": 1 })`
*   **Zašto ova vrsta?** Kada se indeksira polje unutar **niza** (`items`), MongoDB automatski kreira višeključni indeks. On ne indeksira sam niz, već **svaki pojedinačni element** unutar niza.
*   **Šta omogućava?** Munjevito brzo pretraživanje transakcija na osnovu sadržaja niza. Omogućava efikasne odgovore na pitanja kao što su:
    *   "Pronađi sve transakcije u kojima je kupljen bar jedan proizvod iz kategorije 'Coffee'."
    *   "Koliki je ukupan prihod od proizvoda iz kategorije 'Pastry'?"