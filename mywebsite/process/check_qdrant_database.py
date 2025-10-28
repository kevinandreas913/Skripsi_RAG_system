from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import json

# # ------------------- TRY CONNECTION QDRANT -------------------
# # Inisialisasi client
# client = QdrantClient("127.0.0.1", port=6333)

# try:
#     collections = client.get_collections()
#     print("Koneksi ke Qdrant: BERHASIL")
# except Exception as e:
#     print(f"Koneksi ke Qdrant: GAGAL\nError: {e}")

# # ------------------- CEK DATABASE LAMA QDRANT -------------------

# client = QdrantClient(host="127.0.0.1", port=6333)
# print(client.get_collections())

# ------------------- SETUP QDRANT -------------------

client = QdrantClient(host="127.0.0.1", port=6333)
collection_name = "pdf_embeddings"

info = client.get_collection(collection_name=collection_name)
print(f"Total Points Tersimpan: {info.points_count}\n")

# AMBIL SEMUA DATA 

# Kalau mau filter berdasarkan user_id, isi variabel berikut
filter_user_id = None  # contoh: "user_a"  -> Kalau None berarti ambil semua

scroll_filter = None
if filter_user_id:
    scroll_filter = Filter(
        must=[
            FieldCondition(key="user_id", match=MatchValue(value=filter_user_id))
        ]
    )

next_page = None
total_data = 0

print("===== DATA QDRANT =====")
while True:
    response = client.scroll(
        collection_name=collection_name,
        scroll_filter=scroll_filter,
        limit=100,  # Ambil 100 data per iterasi
        offset=next_page
    )

    points, next_page = response
    if not points:
        break

    for point in points:
        total_data += 1
        print(f"ID: {point.id}")
        print(f"User ID: {point.payload.get('user_id')}")
        print(f"PDF ID: {point.payload.get('pdf_id')}")
        print(f"Teks: {point.payload.get('text')[:100]}...")  # Print sebagian teks
        print("=" * 50)

    if next_page is None:
        break

print(f"\nTotal Data Ditampilkan: {total_data}")


# note: backup belum dicoba, mungkin saja ada error
# # ------------------- BACKUP DATA QDRANT -------------------
# # Inisialisasi koneksi
# client = QdrantClient(host="127.0.0.1", port=6333)
# collection_name = "pdf_embeddings"
# backup_file = f"{collection_name}_backup.json"

# # Scroll semua point (100 per batch)
# scroll_filter = None  # Bisa disesuaikan kalau mau filter tertentu
# next_page = None
# all_data = []

# while True:
#     response = client.scroll(
#         collection_name=collection_name,
#         scroll_filter=scroll_filter,
#         limit=100,
#         offset=next_page,
#         with_payload=True,
#         with_vectors=True,
#     )

#     points, next_page = response
#     if not points:
#         break

#     for point in points:
#         data = {
#             "id": point.id,
#             "vector": point.vector,
#             "payload": point.payload
#         }
#         all_data.append(data)

#     if next_page is None:
#         break

# # Simpan ke file JSON
# with open(backup_file, "w", encoding="utf-8") as f:
#     json.dump(all_data, f, indent=2, ensure_ascii=False)

# print(f"✅ Backup selesai. Total {len(all_data)} data disimpan ke: {backup_file}")


# # ------------------- DELETE ALL DATA QDRANT -------------------
# client = QdrantClient(host="127.0.0.1", port=6333)
# collection_name = "pdf_embeddings"

# client.delete_collection(collection_name=collection_name)
# print("Collection berhasil dihapus.")