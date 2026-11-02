# Pertumbuhan Anak

Aplikasi pencatatan pertumbuhan anak berdasarkan pengukuran tinggi dan berat badan.

## Fitur


- Tambah banyak anak
- Biodata anak
- Tanggal lahir
- Jenis kelamin
- Pencatatan pengukuran berkala
- Tinggi badan
- Berat badan
- Perhitungan usia dalam bulan otomatis berdasarkan tanggal lahir dan tanggal pengukuran
- Riwayat pengukuran
- Kurva tinggi badan berdasarkan usia
- Kurva berat badan berdasarkan usia
- Kurva referensi WHO (−2 SD, median, +2 SD) berdasarkan jenis kelamin
- Edit seluruh biodata anak
- Hapus anak beserta seluruh riwayat pengukuran dengan konfirmasi
- Edit tanggal, tinggi, berat, dan catatan pengukuran
- Hapus pengukuran dengan konfirmasi
- Usia pengukuran otomatis dihitung ulang jika tanggal lahir anak berubah
- Mencegah dua pengukuran pada tanggal yang sama untuk anak yang sama
- SQLite
- Docker
- Siap di-push ke GitHub

## Menjalankan tanpa Docker

Pastikan Python 3.12+ tersedia.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Buka:

http://locapylhost:5000

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Buka:

http://localhost:5000

## Menjalankan dengan Docker

```bash
docker compose up -d --build
```

Buka:

http://localhost:5000

Melihat log:

```bash
docker compose logs -f
```

Menghentikan:

```bash
docker compose down
```

Data SQLite disimpan pada Docker volume `growth_data`, sehingga container dapat dibuat ulang tanpa menghapus data.

## GitHub

Setelah membuat repository kosong di GitHub:

```bash
git init
git add .
git commit -m "Initial project"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

Jangan commit file `.env` atau database pribadi.

## Kurva pertumbuhan

Pada halaman detail anak, grafik akan dibuat otomatis dari seluruh riwayat pengukuran.
Sumbu X menggunakan usia dalam bulan, bukan nomor urut pengukuran. Tooltip juga menampilkan
tanggal pengukuran.

Chart menggunakan Chart.js dari CDN. Jika aplikasi nantinya harus berjalan sepenuhnya tanpa
internet, Chart.js dapat dipindahkan ke folder `static/vendor`.

## Catatan pengembangan

Versi ini sudah mencakup grafik pertumbuhan, referensi WHO, serta edit/hapus data.
Tahap berikutnya dapat menambahkan:

1. Perhitungan Z-score WHO berbasis LMS.
2. Status pertumbuhan dengan penjelasan yang hati-hati.
3. Foto anak.
4. Login pengguna.
5. Backup dan restore database.
6. Export PDF/Excel.

## Standar WHO

Aplikasi menyimpan referensi WHO secara lokal di `static/data/who_growth_standards.json`.
Grafik menampilkan -2 SD, median, dan +2 SD berdasarkan jenis kelamin.

Sumber referensi: WHO Child Growth Standards (0-5 years), indikator length/height-for-age
dan weight-for-age. Referensi ini digunakan sebagai pembanding pertumbuhan, bukan diagnosis medis.

Catatan penting: WHO membedakan **length** untuk anak di bawah 2 tahun dan **height** untuk usia 2-5 tahun.


## Referensi WHO V5

- 0–60 bulan: WHO Child Growth Standards.
- 61–228 bulan: WHO Growth Reference 2007 untuk tinggi menurut umur.
- 61–120 bulan: WHO Growth Reference 2007 untuk berat menurut umur.
- Berat menurut umur tidak diteruskan setelah 120 bulan karena WHO tidak menyediakan referensi indikator tersebut di atas 10 tahun.
- Kurva 61+ menggunakan titik acuan WHO 2007 dan interpolasi visual antar titik pada grafik.

Sumber resmi: WHO Growth Reference 5–19 years — https://www.who.int/tools/growth-reference-data-for-5to19-years
