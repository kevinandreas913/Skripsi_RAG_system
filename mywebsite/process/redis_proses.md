# Proses redis


## 1. Membuat redis secara otomatis dengan perintah cmd
run
```
docker run -d -p 6379:6379 --name redis redis
docker run -d -p 6379:6379 -v redis_data:/data --name redisqueue redis

```
penjelasan:  
- **-d** "Detached mode" = container jalan di 
background, jadi terminal kamu tidak terganggu.  
- **-p 6379:6379**  
6379 (sebelah kiri) = port di host (komputer/VPS kamu).  
6379 (sebelah kanan) = port di dalam container (port default Redis).  
Artinya: kalau kamu akses localhost:6379 di host, otomatis diteruskan ke Redis di container.
- **-v redis_data:/data** =
redis_data -> nama volume di Docker (persisten, tidak hilang walau container dihapus).
/data -> folder di dalam container Redis tempat data Redis disimpan (default Redis).  
semua database redis disimpan ke volume redis_data, bukan hilang saat container mati.
- **--name redisqueue** = berikan nama container jadi redisqueue (anda dapat bebas memberikan nama).
- Mapping Port   
Port 6379 di container akan dipetakan ke port 6379 di mesin host, sehingga redis dapat diakses di:
```
http://localhost:6379
```
- Volume redis_data   
Volume bernama redis_data akan dibuat (jika belum ada).   
Volume ini berfungsi untuk menyimpan data redis agar tetap aman meskipun container dihentikan atau dihapus.

python manage.py qcluster