# BPS Explorer

Tool web untuk menjelajahi & mengunduh data Web API BPS (Badan Pusat Statistik) lintas domain (nasional/provinsi/kabupaten-kota) — dijalankan lokal.

## Fitur

### Statistik menurut Subjek (tab utama)
- Navigasi sidebar mengikuti klasifikasi **CSA Subject** BPS (Kategori → Subjek), sama seperti struktur di bps.go.id/statistics-table.
- Begitu daftar tabel tampil, link download Excel langsung diresolve otomatis di background (tanpa perlu klik 2x seperti di web BPS aslinya).
- Checkbox multi-select + **Download Terpilih**: beberapa tabel sekaligus dibundel jadi satu file `.zip`.
- **Copy Semua Judul**: salin semua judul tabel yang sedang tampil ke clipboard.
- Filter judul secara instan di sisi client.
- Node **"Cari Semua Tabel"**: pencarian keyword bebas lintas seluruh tabel statis di domain terpilih, untuk menjangkau data yang mungkin tidak masuk kategori CSA manapun.

### Dynamic Data
- Navigasi berjenjang: Kategori Subjek → Subjek → Variabel → Wilayah/Rincian/Tahun, dengan pagination otomatis (semua halaman data BPS diambil, bukan cuma halaman pertama).
- Rekonstruksi otomatis `datacontent` BPS (key gabungan vervar+var+turvar+tahun+turtahun) jadi baris tabel yang mudah dibaca.
- Export hasil ke CSV, Excel (.xlsx), atau JSON.

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

BPS punya dua sistem klasifikasi subjek yang berbeda:
- **Taksonomi dasar** (`subcat`/`subject`) — dipakai untuk menu Dynamic Data (`var`, `vervar`, `turvar`, `th`).
- **CSA Subject** (`subcatcsa`/`subjectcsa`/`tablestatistic`) — dasar tampilan "Statistik menurut Subjek" di website BPS modern, memetakan tabel ke sumber Static Table/Dynamic Table/SIMDASI lewat field `tablesource`.

Untuk tabel bersumber Static Table, tool ini memanggil endpoint lama `Detail Statictable` (`/v1/view?model=statictable&id=...`) memakai `id` yang sama dari listing CSA untuk mengambil link Excel-nya — endpoint ini sudah stabil & terdokumentasi lengkap, jadi tidak bergantung pada skema `Detail of Table (Using CSA Subject)` yang belum terdokumentasi penuh.

Nilai aktual Dynamic Data dikembalikan BPS sebagai `datacontent` dengan key hasil konkatenasi `vervar+var+turvar+tahun+turtahun` — tool ini merekonstruksi key tersebut dari kombinasi label yang tersedia.

## Rencana Lanjutan

Fitur "multi-region puller" (ambil 1 variabel Dynamic Data untuk banyak domain sekaligus, mis. semua provinsi) direncanakan menyusul.

## Lisensi

MIT
