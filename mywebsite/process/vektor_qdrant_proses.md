
# Proses qdrant

## 1. Membuat qdrant secara manual (docker-compose.yml) dengan direktori lokal 
buat file docker-compose.yml kemudian masukkan ini
```  
version: "3.8"

services:
  qdrant:
    image: qdrant/qdrant
    container_name: qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_data:
```

proses menjalankan docker-compose.yml dapat menggunakan perintah
```
docker-compose up -d
```

Cek container apakah sudah berjalan:
```
docker ps
```
atau 
```
docker -p
```
Contoh output kalau berhasil:
``` python
>>> CONTAINER | ID | IMAGE | COMMAND | CREATED | STATUS | PORTS | NAMES
>>> xxxxxxx | qdrant/qdrant:latest | "./entrypoint.sh" | X seconds ago | Up X seconds | 0.0.0.0:6333->6333/tcp, [::]:6333->6333/tcp | qdrant
```

## 2. Membuat Qdrant secara otomatis dengan perintah cmd
run
```
docker run -d -p 6333:6333 -v qdrant_data:/qdrant/storage --name qdrantdatabase qdrant/qdrant
```
- **-d** "Detached mode" = container jalan di 
background, jadi terminal kamu tidak terganggu.  
- **-p 6333:6333**  
6333 (sebelah kiri) = port di host (komputer/VPS kamu).  
6333 (sebelah kanan) = port di dalam container (port default qdrant).  
Artinya: kalau kamu akses localhost:6333 di host, otomatis diteruskan ke qdrant di container.
- **-v qdrant_data:/data** =
qdrant_data -> nama volume di Docker (persisten, tidak hilang walau container dihapus).
/data -> folder di dalam container qdrant tempat data qdrant disimpan.  
semua database qdrant disimpan ke volume qdrant_data, bukan hilang saat container mati.
- **--name qdrantdatabase** = berikan nama container jadi qdrantdatabase (anda dapat bebas memberikan nama).
- Mapping Port   
Port 6333 di container akan dipetakan ke port 6333 di mesin host, sehingga Qdrant dapat diakses di:
```
http://localhost:6333
```
- Volume qdrant_data   
Volume bernama qdrant_data akan dibuat (jika belum ada) dan dipasang ke direktori **/qdrant/storage** di dalam container.   
Volume ini berfungsi untuk menyimpan data Qdrant agar tetap aman meskipun container dihentikan atau dihapus.
---
Jika ingin memastikan images qdrant/qdrant adalah yang terbaru maka dapat menggunakan perintah
```
docker pull qdrant/qdrant
```


## 3. Cek Koneksi ke Qdrant dari Python
Pastikan library qdrant-client sudah terinstall:
```python
pip install qdrant-client
```
Lalu buat skrip Python untuk cek koneksi:
```python
from qdrant_client import QdrantClient

# Inisialisasi client
client = QdrantClient("127.0.0.1", port=6333)

try:
    collections = client.get_collections()
    print("Koneksi ke Qdrant: BERHASIL")
except Exception as e:
    print(f"Koneksi ke Qdrant: GAGAL\nError: {e}")
```
pastikan output:
```python
>>> Koneksi ke Qdrant: BERHASIL
```

## 4. Perintah untuk stop dan start
stop
```
docker stop (nama container) 
```
cek apakah sudah benar stop
```
netstat -ano | findstr 6333
```

---
start
```
docker start (nama container)
```

## 4. Perintah untuk backup dari docker
lakukan stop terlebih dahulu jika masih running
```
docker stop (nama container) 
```
cek apakah sudah benar stop
```
netstat -ano | findstr 6333
```

---
masukkan perintah untuk cek daftar container
```
docker ps -a  
```
kemudian akan muncul contoh sebagai berikut
```
CONTAINER ID   IMAGE           COMMAND             CREATED       STATUS                        PORTS     NAMES
899a4d65b29c   qdrant/qdrant   "./entrypoint.sh"   2 weeks ago   Exited (143) 19 seconds ago             qdrantdatabase
```
nama container tersebut adalah **qdrantdatabase**.  
Lakukan backup dengan perintah
```
docker cp {namacontainer}:/qdrant/storage "C:\Users\Acer\Desktop\qdrant_backup_storage"
```
contoh:
```
docker cp qdrantdatabase:/qdrant/storage "C:\Users\Acer\Desktop\qdrant_backup_storage"
```

---
jika di vps linux:
```
sudo docker cp qdrantdatabase:/qdrant/storage /home/username/qdrant_backup_storage
```

# Catatan docker
## Dasar

| Perintah                           | Penjelasan                                  |
|-------------------------------------|---------------------------------------------|
| `docker-compose up -d`             | Jalankan semua service di background.       |
| `docker-compose up`                | Jalankan semua service, log tampil di terminal. |
| `docker-compose down`              | Matikan & hapus semua container & network.  |
| `docker-compose ps`                | Lihat daftar container dari compose.        |
| `docker-compose logs`              | Lihat log semua container.                  |
| `docker-compose logs [service]`    | Lihat log service tertentu.                 |
| `docker-compose restart`           | Restart semua service.                      |
| `docker-compose restart [service]` | Restart service tertentu.                   |
| `docker-compose stop`              | Hentikan semua container.                   |
| `docker-compose rm`                | Hapus container yang sudah stop.            |
| `docker stop ...(namacontainer)`   | Stop container lama.                        |
| `docker rm ...(namacontainer)`     | Hapus container lama.                        |
---

## Build & Image

| Perintah                           | Penjelasan                                  |
|-------------------------------------|---------------------------------------------|
| `docker-compose build`              | Build ulang image dari docker-compose.yml.  |
| `docker-compose pull`               | Download image terbaru dari Docker Hub.     |

---

## Opsi Tambahan

| Perintah                           | Penjelasan                                  |
|-------------------------------------|---------------------------------------------|
| `docker-compose config`             | Lihat hasil parsing docker-compose.yml (cek error). |
| `docker-compose down -v`            | Stop & hapus semua container dan volume (data hilang). |
| `docker-compose -p [project_name] up -d` | Jalankan dengan nama project custom (prefix nama container berubah). |

---

## Bersih-Bersih Docker (opsional)

| Perintah                           | Penjelasan                                  |
|-------------------------------------|---------------------------------------------|
| `docker system prune -a`            | Bersihkan semua container, image, network tidak terpakai (hati-hati!). |

---

**Catatan:**  
- Pastikan di direktori yang berisi `docker-compose.yml` saat menjalankan perintah ini.
- `-d` artinya detached mode (tidak menampilkan log di terminal).
- Gunakan `docker-compose logs` untuk melihat log setelahnya.



