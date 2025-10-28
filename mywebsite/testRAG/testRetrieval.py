# Pastikan impor ini ada di bagian atas file Anda
from sentence_transformers import SentenceTransformer, util
from qdrant_client import QdrantClient
# Impor model yang diperlukan untuk filtering
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import numpy as np

# --- Fungsi Evaluasi dari Dokumen Anda (Tetap sama) ---
def evaluasi_relevansi_retriever(pertanyaan: str, konteks_diambil: list[str], model: SentenceTransformer) -> dict:
    """
    [cite_start]Mengevaluasi relevansi konteks yang diambil terhadap sebuah pertanyaan menggunakan kemiripan semantik[cite: 61].
    
    Args:
        [cite_start]pertanyaan (str): Pertanyaan asli dari pengguna[cite: 61].
        [cite_start]konteks_diambil (list[str]): Daftar potongan konteks yang diambil oleh sistem RAG[cite: 61].
        model (SentenceTransformer): Model embedding yang sudah di-load.

    Returns:
        [cite_start]dict: Kamus yang berisi skor relevansi rata-rata dan skor individual[cite: 61, 62].
    """
    if not konteks_diambil:
        return {
            "relevansi_konteks_rata_rata": 0.0,
            "skor_konteks_individual": []
        }
        
    embedding_pertanyaan = model.encode(pertanyaan, convert_to_tensor=True)
    embedding_konteks = model.encode(konteks_diambil, convert_to_tensor=True)
    skor_cosine = util.cos_sim(embedding_pertanyaan, embedding_konteks)
    skor_individu = skor_cosine.cpu().tolist()[0] 
    skor_rata_rata = sum(skor_individu) / len(skor_individu) if skor_individu else 0.0

    return {
        "relevansi_konteks_rata_rata": skor_rata_rata,
        "skor_konteks_individual": skor_individu
    }

# --- Fungsi Utama yang Diperbarui ---
def test_retrieval_dan_evaluasi(
    pertanyaan_pengguna: str, 
    client: QdrantClient, 
    model_embedding: SentenceTransformer, 
    collection_name: str, 
    top_k: int = 3,
    pdf_id_filter: str = None  # <-- Parameter baru untuk filter
):
    """
    Melakukan pencarian di Qdrant dan mengevaluasi hasilnya.
    Dapat memfilter berdasarkan pdf_id jika disediakan.
    """
    print(f"🔍 Mencari jawaban untuk pertanyaan: '{pertanyaan_pengguna}'")
    if pdf_id_filter:
        print(f"   (Dibatasi pada PDF ID: {pdf_id_filter})")
    print("-" * 50)

    # 1. Embed pertanyaan pengguna
    query_embedding = model_embedding.encode(pertanyaan_pengguna, normalize_embeddings=True)

    # 2. Siapkan filter jika pdf_id_filter diberikan
    query_filter = None
    if pdf_id_filter:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="pdf_id",  # Nama field di payload
                    match=MatchValue(value=pdf_id_filter) # Nilai yang ingin dicocokkan
                )
            ]
        )

    # 3. Lakukan pencarian di Qdrant dengan filter opsional
    search_results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        query_filter=query_filter,  # <-- Terapkan filter di sini
        limit=top_k
    )

    # 4. Kumpulkan konteks yang berhasil diambil
    konteks_diambil = [result.payload['text'] for result in search_results]
    
    if not konteks_diambil:
        print("Tidak ada konteks yang ditemukan di database (dengan filter yang diberikan).")
        return

    # Sisa kode tetap sama...
    print(f"{len(konteks_diambil)} Konteks Teratas yang Diambil:")
    for i, konteks in enumerate(konteks_diambil):
        print(f"  [{i+1}] {konteks[:150]}...")
    print("-" * 50)
    
    hasil_evaluasi = evaluasi_relevansi_retriever(pertanyaan_pengguna, konteks_diambil, model_embedding)

    print("📊 Hasil Evaluasi Relevansi Konteks:")
    print(f"   Skor Rata-rata: {hasil_evaluasi['relevansi_konteks_rata_rata']:.4f}")
    print("   Skor Individual per Konteks:")
    for i, skor in enumerate(hasil_evaluasi['skor_konteks_individual']):
        print(f"     - Konteks {i+1}: {skor:.4f}")

    return {
        "konteks_diambil": konteks_diambil,
        "evaluasi": hasil_evaluasi
    }

# -------------------- CONTOH PENGGUNAAN BARU --------------------
if __name__ == "__main__":
    client = QdrantClient(host="127.0.0.1", port=6333)
    collection_name = "pdf_embeddings"
    model_embedding = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    # ID PDF spesifik yang ingin Anda cari
    pdf_id_spesifik = "q4jLV1jetmqq29sYiVju8LEVQeqpXHgSxpK5wkEdF4c"
    
    pertanyaan_untuk_diuji = "Apa nama prinsip yang melarang lebih dari satu elektron menduduki keadaan energi kuantum yang sama?"
    
    # Jalankan fungsi tes dengan menyertakan pdf_id_filter
    test_retrieval_dan_evaluasi(
        pertanyaan_pengguna=pertanyaan_untuk_diuji,
        client=client,
        model_embedding=model_embedding,
        collection_name=collection_name,
        top_k=3,
        pdf_id_filter=pdf_id_spesifik 
    )