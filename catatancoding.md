# isi:

1. [Langkah Django dalam mendaftar / membuat Pengguna Baru](#1-langkah-django-dalam-mendaftar--membuat-pengguna-baru)
2. [Langkah Django dalam login Pengguna](#2-langkah-django-dalam-login-pengguna)
3. [Keterkaitan AbstractBaseUser, BaseUserManager, PermissionsMixin](#3-keterkaitan-abstractbaseuser-baseusermanager-permissionsmixin)
4. [Tentang fungsi "user = authenticate(request, username=username, password=password)" dan penggunaan dalam views untuk halaman lain](#4-tentang-fungsi-user--authenticaterequest-usernameusername-passwordpassword-dan-penggunaan-dalam-views-untuk-halaman-lain)
5. [Tentang proses pagination](#5-tentang-proses-pagination)
6. [OTP Email](#6-otp-email)
7. [with transaction.atomic()](#7-with-transactionatomic)
8. [Cara kerja queue - django-q](#8-cara-kerja-queue---django-q)
 
---

## 1. Langkah Django dalam mendaftar / membuat Pengguna Baru
Langkah-langkah saat pendaftaran atau pembuatan pengguna:
- Input Data:
Pengguna mengisi form dengan username dan password (atau data lain jika diperlukan) pada form pendaftaran di tampilan (misalnya, register.html).

- Kirim Data ke Backend:
Data form dikirim ke views.py (melalui HTTP POST).
Misalnya, URL untuk registrasi menggunakan POST adalah /register/.

- Menggunakan UserManager untuk Membuat Pengguna Baru:
Di views.py, Anda akan menangani data form dan mengirimnya untuk membuat pengguna baru.

- UserManager yang sudah Anda buat menyediakan dua metode utama: create_user() dan create_superuser().
Jika pengguna adalah pengguna biasa, Anda akan menggunakan create_user() untuk membuat pengguna dengan username dan password yang dimasukkan.
Password akan secara otomatis di-hash saat disimpan dengan menggunakan set_password().

- Metode create_user():
Validasi username: Jika username kosong, akan muncul error.
Hash Password: Password yang dimasukkan oleh pengguna akan di-hash menggunakan set_password() sebelum disimpan ke database.
Simpan Pengguna: Pengguna baru disimpan ke database menggunakan user.save().

- Penyimpanan di Database:
Setelah berhasil membuat pengguna, data disimpan dalam tabel TbUser, dengan password yang di-hash dan username yang unik.

---

## 2. Langkah Django dalam login Pengguna
Setelah pengguna terdaftar, mereka akan login menggunakan username dan password.
Langkah-langkah saat login:
- Input Data Login:
Pengguna mengisi username dan password di form login dan mengirimnya ke backend (misalnya, di URL /login/).

- Validasi Login di Backend:
Setelah data login dikirim, backend (di views.py) akan mencoba untuk mencocokkan data username dan password yang dimasukkan dengan data yang ada di database.
Django menggunakan authenticate() untuk mencocokkan username dan password. Fungsi ini akan memeriksa apakah password yang dimasukkan cocok dengan hash password yang ada di database.

- Autentikasi dengan authenticate():
Django akan memeriksa apakah password yang dimasukkan sesuai dengan hash password yang tersimpan di database. Fungsi ini akan mengembalikan objek user jika login berhasil, atau None jika login gagal.
Jika login berhasil, pengguna akan diautentikasi menggunakan django_login(), yang menetapkan pengguna ke sesi.

- Set Sesi Pengguna:
Sesi pengguna disimpan di session dengan menambahkan user_id dan username ke dalam session:
request.session['user_id'] = str(user.id)
request.session['username'] = user.username

- Redirect ke Dashboard atau Halaman Tertentu:
Jika login berhasil, pengguna diarahkan ke halaman yang sudah ditentukan (misalnya, dashboard). Jika gagal, pesan error ditampilkan.

---

## 3. Keterkaitan Abstractbaseuser Baseusermanager Permissionsmixin
- AbstractBaseUser:
Menyediakan kerangka dasar untuk model pengguna Anda.
Mengatur password, memeriksa password, dan mencatat waktu login.

- BaseUserManager:
Menyediakan cara membuat pengguna (create_user dan create_superuser) dengan menggunakan logika yang sesuai dengan model Anda.
Misalnya, mengatur password dengan set_password() dari AbstractBaseUser.

- PermissionsMixin:
Menambahkan kemampuan untuk mengelola izin dan kelompok pengguna.
Digunakan untuk memastikan bahwa superuser memiliki semua izin (is_superuser=True).

---

## 4. Tentang fungsi "user = authenticate(request, username=username, password=password)" dan penggunaan dalam views untuk halaman lain
- authenticate berarti bahwa ketika login maka akan melakukan authentikasi atas username dan password berdasarkan username dan password yang telah didaftarkan dan dicocokkan dengan username dan password yang diperoleh dari request.
- proses authenticate akan disimpan kedalam variabel yang bernama "user".
- Ketika pengguna masuk ke halaman lain seperti '/dashboard' atau '/tambahkolom' atau lainnya, pengguna masih tetap terkoneksi dengan data authentikasi yang disimpan dalam variabel "user" tersebut sehingga pengguna dapat mengakses id, username, dan password sebagaimana dalam tabel user yang telah terdaftar. 
- Contoh dalam mengakses data "id" tersebut, pengguna cukup menggunakan perintah "request.user". 
- Contoh dalam mengakses data "username" tersebut, pengguna cukup menggunakan perintah "request.user.username". 

---

## 5. Proses pagination
- proses pagination pada views.py (def newcoloumn(request):):
    "kolom_data = TbAdditional.objects.filter(user_id=request.user)"
    berarti memanggil semua data dalam TbAdditional dengan filter sesuai dengan user_id yang terdapat di request.user, semua data kemudian ditampung daam "kolom_data"

    "halaman = Paginator(kolom_data, 1)"
    data yang sudah ada kemudian digunakan fungsi Paginator dengan maksimal 1 halaman tabel adalah 1 data saja.

    "page_number = request.GET.get('page',1)"
    page_number digunakan untuk menangkap nomor halaman dari URL parameter ?page=<number>.
        request.GET.get('page', 1) mencari parameter page dalam permintaan GET.
        Jika parameter page tidak ada, nilai default yang digunakan adalah 1, yang berarti halaman pertama.

    "try:
        data = halaman.page(page_number)"
    Bagian ini mencoba mengambil halaman sesuai dengan nomor halaman yang didapat dari page_number. Metode halaman.page(page_number) akan menampilkan data untuk halaman tersebut.

    "except PageNotAnInteger:
        data = halaman.page(1)"
    Jika nilai page_number bukan angka yang valid (misalnya karakter atau string selain angka), maka blok ini menangani pengecualian PageNotAnInteger. Dalam situasi ini, kode akan menampilkan halaman pertama dengan halaman.page(1).

    "except EmptyPage:
        data = halaman.page(halaman.num_pages)"
    Jika nilai page_number lebih besar dari jumlah halaman yang tersedia (melebihi batas), blok ini menangani pengecualian EmptyPage. Dalam situasi ini, kode akan menampilkan halaman terakhir dengan halaman.page(halaman.num_pages).

    "context = {
        'kolom_data': data,
    }"
    Kompres data ke dalam variabel 'kolom_data' yang nantinya siap digunakan dalam html

- atribut pada pagination untuk html dapat diakses melalui ini (https://medium.com/django-unleashed/user-friendly-django-pagination-5db4658b80ae)
    page_obj.has_previous: Mengecek apakah ada halaman sebelumnya.
        "True" jika ada halaman sebelum halaman saat ini.
    page_obj.has_next: Mengecek apakah ada halaman berikutnya.
        "True" jika ada halaman setelah halaman saat ini.
    page_obj.previous_page_number: Mengembalikan nomor halaman sebelumnya.
        Nomor halaman sebelum halaman yang sedang dibuka.
    page_obj.next_page_number: Mengembalikan nomor halaman berikutnya.
        Nomor halaman setelah halaman yang sedang dibuka.
    page_obj.number: Mengembalikan nomor halaman saat ini.
        Menunjukkan halaman yang sedang aktif.
    page_obj.paginator: Mengembalikan instance dari kelas Paginator.
        Mengakses objek pengelola pagination.
    page_obj.paginator.num_pages: Mengembalikan jumlah total halaman.
        Total banyaknya halaman yang tersedia.
    page_obj.paginator.page_range: Mengembalikan daftar (range) nomor halaman.
        Rentang semua nomor halaman dari 1 sampai total halaman.

- pada html 
    1. Cek apakah ada halaman lain ({% if kolom_data.has_other_pages %})
    kolom_data.has_other_pages memastikan pagination hanya ditampilkan jika jumlah data melebihi satu halaman.

    2. Tombol "sebelumnya" ({% if kolom_data.has_previous %})
    Jika ada halaman sebelumnya (kolom_data.has_previous), tombol untuk halaman sebelumnya akan muncul.
    Jika tidak ada, tombol "sebelumnya" akan dinonaktifkan.
    
    3. Tanda ellipsis ("...") sebelum halaman ({% if kolom_data.number|add:'-4' > 1 %} dan 
                                                {% if kolom_data.paginator.num_pages > kolom_data.number|add:'4' %} )
    Ditampilkan jika ada lebih dari 4 halaman sebelum halaman aktif untuk menyembunyikan halaman awal.
    
    4. Menampilkan nomor halaman dalam rentang tertentu ({% for i in kolom_data.paginator.page_range %} dan
                                    {% if kolom_data.number == i %} dan 
                                    {% elif i > kolom_data.number|add:'-5' and i < kolom_data.number|add:'5' %} dan
                                    {% elif i > kolom_data.number and i <= kolom_data.number|add:'4' %})
    Halaman aktif ditampilkan dengan gaya khusus (active).
    Halaman di sekitar (maksimum 4 halaman setelah dan sebelum halaman aktif) juga ditampilkan.
    Ellipsis tambahan muncul sebelum halaman terakhir jika ada banyak halaman di depan.
    
    5. Tombol "berikutnya" ({{% if kolom_data.has_next %}})
    Jika ada halaman berikutnya (kolom_data.has_next), tombol akan muncul untuk berpindah ke halaman berikutnya.
    Jika tidak ada, tombol "berikutnya" dinonaktifkan.

---

## 6. otp email
"https://dev.to/rupesh_mishra/implementing-email-and-mobile-otp-verification-in-django-a-comprehensive-guide-4oo0"

---

## 7. with transaction.atomic()
seluruh proses berjalan, apabila sudah berjalan maka akan berhasil, tetapi jika di awal proses berjalan dengan baik dan di tengah tiba-tiba ada masalah maka proses diawal juga tidak akan dieksekusi. contoh:
    with transaction.atomic():

        apis = TbAPI.objects.filter(user=user)                <----- berjalan baik
        for api in apis:                                      <----- berjalan baik
            delete_qdrant_data(api.api_key)                   <----- berjalan baik

        additions = TbAPI.objects.filter(user=user)           <----- berjalan baik
        for obj in additions:                                 <----- berjalan baik
            superuserdeletfile(obj.file)                      <----- berjalan baik
        additions.delete()                                    <----- berjalan baik

        superuserdeletfile(user.profile)                      <----- gagal

        apis.delete() 

        user.delete()

---

## 8. cara kerja queue - django-q
```
Q_CLUSTER = {
    "name": "qcluster",
    "workers": 4, 
    "recycle": 500,
    "timeout": 300, 
    "queue_limit": 50,
    "bulk": 10,
    "broker_class": "django_q.brokers.redis_broker.Redis",
    "retry": 120,
    "ack_failures": True,
    "catch_up": False,
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    }
}
```
- name = nama
- workers = jumlah proses yang berjalan secara palarel. Seperti 4 orang tukang yang bekerja dalam menyelesaikan 10 tugas.
- recycle = berapa taks per worker (default 500). Setelah seorang tukang sudah mengerjakan 500 tugas, dia istirahat (dikeluarkan dan diganti yang baru).
- timeout = batas detik per task untuk sebelum workers mematikan taks tersebut (default = none). Maksimal waktu tunggu tiap tugas adalah 300 detik (5 menit).
- queue_limit = membatasi banyak task yang ditarik dan disimpan di memori oleh satu klaster. Bayangkan antrian panjang. Tapi supaya tidak numpuk, maksimal hanya 50 tugas yang boleh ngantri.
- bulk = banyak pesan yang coba diambil per panggila untuk efisiensi broker. Para tukang tadi mengambil tugas dari antrian 10 sekaligus biar hemat waktu, bukan satu-satu.
- broker_class = tempat menyimpan broker.
Redis ibarat papan tulis yang dipakai semua tukang untuk ambil antrian tugas.
- retry = detik yang ditunggu broker sebelum menggagap taks belum tuntas. Kalau ada tugas gagal, tunggu 120 detik (2 menit) sebelum dicoba lagi.
- ack_failures = jika true, kegagalan juga di-ack (dianggap “terkirim”) sehingga task gagal dihapus dari antrean broker dan tidak akan dikirim ulang otomatis. Jika True, ketika tugas gagal, dicatat di buku laporan (database).
- catch_up = Jika klaster mati lama dan ada jadwal yang terlewat, default-nya akan “mengejar ketertinggalan” (menjalankan slot yang terlewat satu per satu). Set False agar saat klaster hidup lagi, schedule hanya jalan sekali lalu kembali normal. Jika False, kalau server sempat mati beberapa jam, Django-Q tidak akan mengerjakan semua tugas lama yang ketinggalan.


karena superuserdeletfile(user.profile) = gagal, maka seluruh proses yang berjalan baik juga akan dianggap tidak pernah dieksekusi