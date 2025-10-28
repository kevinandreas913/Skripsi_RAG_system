import torch
from sentence_transformers import SentenceTransformer, util
import nltk
import numpy as np

# Unduh model tokenizer kalimat dari NLTK (hanya perlu dilakukan sekali)
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Mengunduh tokenizer 'punkt' dari NLTK...")
    nltk.download('punkt')
    print("Unduhan selesai.")

# --- Fungsi Evaluasi dari Dokumen Anda (Bagian 3.2) ---
def evaluasi_keterlandasan_generator(jawaban_dihasilkan: str, konteks_diambil: list[str], model: SentenceTransformer) -> dict:
    """
    [cite_start]Mendekati kesesuaian fakta (faithfulness) dari jawaban yang dihasilkan terhadap konteksnya[cite: 106].
    "Skor Keterlandasan" ini mengukur apakah setiap kalimat dalam jawaban didukung
    [cite_start]secara semantik oleh salah satu potongan konteks yang diambil[cite: 106, 108].
    
    Args:
        [cite_start]jawaban_dihasilkan (str): Jawaban akhir dari generator sistem RAG[cite: 114].
        [cite_start]konteks_diambil (list[str]): Daftar potongan konteks yang diberikan kepada generator[cite: 114].
        model (SentenceTransformer): Model embedding yang sudah di-load.

    Returns:
        dict: Kamus yang berisi skor keterlandasan rata-rata dan skor individual
              [cite_start]untuk setiap kalimat dalam jawaban[cite: 114].
    """
    if not jawaban_dihasilkan or not konteks_diambil:
        return {
            "skor_keterlandasan_rata_rata": 0.0,
            "skor_keterlandasan_kalimat": {}
        }

    # [cite_start]1. Pisahkan jawaban yang dihasilkan menjadi kalimat-kalimat individual (klaim)[cite: 110, 117].
    kalimat_jawaban = nltk.sent_tokenize(jawaban_dihasilkan)
    
    # [cite_start]2. Hasilkan embedding untuk kalimat jawaban dan potongan konteks[cite: 118].
    embedding_kalimat = model.encode(kalimat_jawaban, convert_to_tensor=True)
    embedding_konteks = model.encode(konteks_diambil, convert_to_tensor=True)

    # 3. Hitung matriks kemiripan antara semua kalimat jawaban dan semua konteks.
    matriks_cos_sim = util.cos_sim(embedding_kalimat, embedding_konteks)

    # [cite_start]4. Untuk setiap kalimat jawaban, temukan skor kemiripan tertingginya[cite: 119].
    # Ini adalah nilai maksimum di setiap baris matriks.
    skor_maksimum_per_kalimat = torch.max(matriks_cos_sim, dim=1).values.cpu().tolist()
    
    # [cite_start]5. Skor akhir adalah rata-rata dari skor-skor maksimum ini[cite: 121].
    skor_rata_rata = np.mean(skor_maksimum_per_kalimat) if skor_maksimum_per_kalimat else 0.0

    return {
        "skor_keterlandasan_rata_rata": skor_rata_rata,
        "skor_keterlandasan_kalimat": dict(zip(kalimat_jawaban, skor_maksimum_per_kalimat))
    }

# --- Fungsi Utama untuk Menjalankan Tes ---
def test_generator_keterlandasan(konteks: list[str], jawaban: str, model_embedding: SentenceTransformer):
    """
    Menjalankan dan menampilkan hasil evaluasi keterlandasan.
    """
    print("📝 Jawaban yang Dihasilkan untuk Dievaluasi:")
    print(f'   "{jawaban}"')
    print("\n📦 Konteks yang Diberikan:")
    for i, ctx in enumerate(konteks):
        print(f"   [{i+1}] {ctx}")
    print("-" * 50)

    # Jalankan evaluasi
    hasil_evaluasi = evaluasi_keterlandasan_generator(jawaban, konteks, model_embedding)
    
    # Tampilkan hasil
    print("📊 Hasil Evaluasi Keterlandasan (Groundedness):")
    print(f"   Skor Rata-rata: {hasil_evaluasi['skor_keterlandasan_rata_rata']:.4f}")
    print("   Skor Individual per Kalimat:")
    for kalimat, skor in hasil_evaluasi['skor_keterlandasan_kalimat'].items():
        print(f'     - "{kalimat}" → Skor: {skor:.4f}')
        if skor < 0.6: # Angka ambang batas bisa disesuaikan
            print("       ⚠️  Peringatan: Kalimat ini mungkin tidak didukung kuat oleh konteks (potensi halusinasi).")

# -------------------- CONTOH PENGGUNAAN --------------------
if __name__ == "__main__":
    # Inisialisasi model embedding
    model_embedding = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # Siapkan konteks yang relevan
    konteks_uji = [
        "Perusahaan Gustave Eiffel merancang Menara Eiffel, yang merupakan sebuah monumen ikonik di Paris.",
        "Konstruksi menara ini selesai pada bulan Maret tahun 1889 untuk Pameran Dunia."
    ]

    print("===== Skenario 1: Jawaban Sesuai Fakta (Faithful) =====")
    jawaban_sesuai_fakta = "Menara Eiffel terletak di Paris dan dirancang oleh perusahaan Gustave Eiffel. Pembangunannya selesai pada Maret 1889."
    test_generator_keterlandasan(konteks_uji, jawaban_sesuai_fakta, model_embedding)

    print("\n" + "="*25 + "\n")

    print("===== Skenario 2: Jawaban dengan Halusinasi =====")
    jawaban_halusinasi = "Menara Eiffel ada di Paris dan selesai pada Maret 1889. Menara ini awalnya dicat dengan warna emas."
    test_generator_keterlandasan(konteks_uji, jawaban_halusinasi, model_embedding)