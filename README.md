# BPS Explorer

Tool web untuk menjelajahi & mengunduh data Web API BPS (Badan Pusat Statistik) lintas domain (nasional/provinsi/kabupaten-kota) — dijalankan lokal.

## Fitur

- Navigasi sidebar mengikuti klasifikasi **CSA Subject** BPS (Kategori → Subjek), sama seperti struktur di bps.go.id/statistics-table.
- Begitu daftar tabel tampil, link download Excel langsung diresolve otomatis di background (tanpa perlu klik 2x seperti di web BPS aslinya).
- Checkbox multi-select + **Download Terpilih**: beberapa tabel sekaligus dibundel jadi satu file `.zip`.
- **Copy Semua Judul**: salin semua judul tabel yang sedang tampil ke clipboard.
- Filter judul secara instan di sisi client.
- Node **"Cari Semua Tabel"**: pencarian keyword bebas lintas seluruh tabel statis di domain terpilih, untuk menjangkau data yang mungkin tidak masuk kategori CSA manapun.
- Tabel bersumber Dynamic Table/SIMDASI (bukan Static Table) ditandai badge terpisah, bukan link download palsu.

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

## Lisensi

MIT
