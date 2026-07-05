# BPS Explorer

Tool web untuk menjelajahi & mengunduh data Web API BPS (Badan Pusat Statistik) lintas domain (nasional/provinsi/kabupaten-kota) — dijalankan lokal.

## Fitur

- Navigasi sidebar mengikuti klasifikasi **CSA Subject** BPS (Kategori → Subjek), sama seperti struktur di bps.go.id/statistics-table.
- Begitu daftar tabel tampil, link download Excel langsung diresolve otomatis di background (tanpa perlu klik 2x seperti di web BPS aslinya).
- Checkbox multi-select + **Download Terpilih**: beberapa tabel sekaligus dibundel jadi satu file `.zip`.
- **Copy Semua Judul**: salin semua judul tabel yang sedang tampil ke clipboard.
- Filter judul secara instan di sisi client.
- Node **"Cari Semua Tabel"**: pencarian keyword bebas lintas seluruh tabel statis di domain terpilih, untuk menjangkau data yang mungkin tidak masuk kategori CSA manapun.
- Tabel bersumber **Dynamic Table** dapat tombol **"Lihat Data"**: data (wilayah/variabel/tahun/nilai) ditampilkan langsung di modal, dengan export CSV/Excel/JSON.
- Tabel bersumber **SIMDASI** juga dapat tombol **"Lihat Data"**: pilih tahun, data (kategori/variabel/nilai/satuan) ditampilkan di modal, dengan export CSV/Excel/JSON.

API key tidak pernah disimpan ke disk — hanya dipakai saat request berjalan.

## Prasyarat

- Python 3.9+
- API key (APP ID) dari [Web API BPS](https://webapi.bps.go.id/) (daftar via akun BPS).

## Instalasi & Menjalankan

```bash
pip install -r requirements.txt
python app.py
```

Buka `http://localhost:5002`, masukkan API key BPS, lalu jelajahi datanya.

## Cara Kerja

Tampilan "Statistik menurut Subjek" di website BPS modern (bps.go.id/statistics-table) dibangun di atas klasifikasi **CSA Subject** (`subcatcsa`/`subjectcsa`/`tablestatistic`) — sistem taksonomi terpisah dari `subcat`/`subject` dasar yang dipakai Dynamic Data. Listing `tablestatistic` memetakan tiap tabel ke sumbernya lewat field `tablesource` (1 = Static Table, 2 = Dynamic Table, 3 = SIMDASI).

`id` yang dikembalikan listing CSA adalah base64 dari `"<table_id>#<n>"` (bukan `table_id` polos), jadi untuk mengambil link Excel-nya tool ini memanggil endpoint resmi **Detail of Table (Using CSA Subject)** (`/v1/api/view?model=tablestatistic&id=...`) — endpoint ini langsung mengembalikan `excel`, `size`, dan `updt_date` dalam satu response.

Link Excel dari BPS disajikan lewat script dinamis (`download.php?f=...`), bukan path file statis, jadi ekstensi file yang benar (`.xls`/`.xlsx`) diambil dari header `Content-Disposition` responsnya, bukan ditebak dari URL.

Untuk **Dynamic Table** (`tablesource == 2`), endpoint Detail of Table (Using CSA Subject) yang sama ternyata langsung mengembalikan `var`/`vervar`/`turvar`/`tahun`/`datacontent` di response-nya — jadi datanya diproses ulang lewat parser Dynamic Data yang sama, tanpa perlu query terpisah.

Untuk **SIMDASI** (`tablesource == 3`), `id` dari listing CSA adalah token terenkripsi yang tidak kompatibel dengan endpoint CSA manapun (selalu error 500 di sisi BPS). Tool ini malah memakai jalur endpoint SIMDASI khusus: **List of SIMDASI Table Based on Area and Subject** (`id_subjek` = id subjek CSA / `mms_id`) untuk dapat `id_tabel` + tahun tersedia, lalu **Detail of SIMDASI Table** untuk data aktualnya. Kode wilayah SIMDASI (7 digit MFD, mis. `3100000` untuk DKI Jakarta) diturunkan dari kode domain BPS API (4 digit) dengan menambah `"000"`. Karena listing CSA dan listing SIMDASI adalah dua sistem terpisah, tabel dicocokkan lewat kemiripan judul (title matching setelah dibersihkan dari tag HTML).

## Lisensi

MIT
