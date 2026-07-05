# BPS Explorer

Tool web sederhana untuk menjelajahi Web API BPS (Badan Pusat Statistik) — Dynamic Data (statistik time-series lintas domain nasional/provinsi/kabupaten-kota) dan Static Table — dijalankan lokal.

## Fitur

- Navigasi berjenjang: pilih tipe domain (Nasional/Provinsi/Kabupaten-Kota) → Kategori Subjek → Subjek → Variabel → Wilayah/Rincian/Tahun.
- Pencarian Static Table (tabel Excel siap pakai) per domain, dengan filter keyword & tahun.
- Rekonstruksi otomatis `datacontent` BPS (key gabungan vervar+var+turvar+tahun+turtahun) jadi baris tabel yang mudah dibaca.
- Export hasil ke CSV, Excel (.xlsx), atau JSON.
- API key tidak pernah disimpan ke disk.

## Prasyarat

- Python 3.9+
- API key dari [Web API BPS](https://webapi.bps.go.id/) (daftar via akun BPS).

## Instalasi & Menjalankan

```bash
pip install -r requirements.txt
python app.py
```

Buka `http://localhost:5001`, masukkan API key BPS, lalu jelajahi datanya.

## Cara Kerja

BPS API mengekspos data lewat endpoint generik `/v1/api/list/?model=...` (subject, subcat, var, vervar, turvar, th, statictable) dengan parameter `domain` (kode wilayah 4 digit: `0000` nasional, `1100` dst provinsi, kode kab/kota turunannya). Nilai aktual dynamic data dikembalikan sebagai `datacontent` dengan key hasil konkatenasi `vervar+var+turvar+tahun+turtahun` — tool ini merekonstruksi key tersebut dari kombinasi label yang tersedia agar hasilnya berupa tabel biasa (wilayah, variabel, rincian, tahun, nilai).

## Rencana Lanjutan

Versi ini fokus ke Dynamic Data + Static Table dengan pencarian per-domain. Fitur "multi-region puller" (ambil 1 variabel untuk banyak domain sekaligus, mis. semua provinsi) direncanakan menyusul.

## Lisensi

MIT
