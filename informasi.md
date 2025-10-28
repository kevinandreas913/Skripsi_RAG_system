# PUSAT INFORMASI PENTING



## Informasi Sensitif yang Harus Dikeluarkan Sebelum Deploy

| Bagian                   | Contoh                                              | Alasan                                                                 |
|--------------------------|-----------------------------------------------------|------------------------------------------------------------------------|
| **SECRET_KEY**           | `SECRET_KEY = 'django-insecure-xyz...'`              | Ini kunci utama Django, kalau bocor orang bisa memalsukan session & token. |
| **Database Credentials** | `DATABASES = { 'USER': 'user', 'PASSWORD': 'pass', ... }` | Bisa dipakai orang untuk akses database kamu.                         |
| **Email SMTP Credentials** | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`            | Bisa dipakai orang untuk mengirim email spam pakai akunmu.             |
| **API Keys**             | API Google Maps, OpenAI, dsb.                        | Bisa digunakan orang tanpa batas.                                     |
| **Debug Mode**           | `DEBUG = True` → ubah jadi `False`                    | Kalau `True`, error page akan menampilkan detail server & variabel.   |
| **Allowed Hosts**        | `ALLOWED_HOSTS`                                       | Pastikan diisi domain/IP VPS kamu.                                    |
