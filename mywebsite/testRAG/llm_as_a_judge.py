# -*- coding: utf-8 -*-

# -------------------- IMPORTS UTAMA --------------------
import os
import re
import uuid
import json
import fitz  # PyMuPDF
import torch
import nltk

from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, MarianMTModel, MarianTokenizer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue
from langdetect import detect

# Download necessary NLTK data if not present
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# -------------------- KONFIGURASI GLOBAL --------------------
QDRANT_HOST = "127.0.0.1"
QDRANT_PORT = 6333
# Menggunakan nama koleksi baru untuk evaluasi agar tidak tercampur
COLLECTION_NAME = "pdf_embeddings" 
VECTOR_SIZE = 384  # Sesuai dengan model paraphrase-multilingual-MiniLM-L12-v2

# -------------------- PEMUATAN MODEL SEKALI JALAN --------------------
print("Memuat model-model yang diperlukan...")
# Model untuk embedding teks
model_embedding = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

# Model untuk generate jawaban (RAG) dan evaluasi (Judge)
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer_seallms = AutoTokenizer.from_pretrained("SeaLLMs/SeaLLMs-v3-1.5B-Chat")
model_seallms = AutoModelForCausalLM.from_pretrained(
    "SeaLLMs/SeaLLMs-v3-1.5B-Chat",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

# Model untuk translasi
tokenizer_translate_entoid = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-id")
model_translate_entoid = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-id")
tokenizer_translate_idtoen = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-id-en")
model_translate_idtoen = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-id-en")
print("Semua model berhasil dimuat.")

def translate_idtoen(text):
    inputs = tokenizer_translate_idtoen(text=[text], return_tensors="pt")
    outputs = model_translate_idtoen.generate(**inputs)
    translate_hasil = tokenizer_translate_idtoen.decode(outputs[0], skip_special_tokens=True)
    return translate_hasil

def translate_entoid(text):
    inputs = tokenizer_translate_entoid(text=[text], return_tensors="pt")
    outputs = model_translate_entoid.generate(**inputs)
    translate_hasil = tokenizer_translate_entoid.decode(outputs[0], skip_special_tokens=True)
    return translate_hasil

################################################################################
### BAGIAN 1: SISTEM RAG (Berdasarkan Kode Anda)
################################################################################

def setup_qdrant_collection():
    """Mendirikan koneksi ke Qdrant dan memastikan collection ada."""
    client = QdrantClient(host="127.0.0.1", port=6333)
    try:
        client.get_collection(collection_name="pdf_embeddings")
        print(f"Koleksi '{COLLECTION_NAME}' sudah ada.")
    except Exception:
        print(f"Membuat koleksi baru: '{COLLECTION_NAME}'")
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
    return client

def embedding_question(pertanyaan):
    embedding_pertanyaan = model_embedding.encode([pertanyaan], normalize_embeddings=True)
    return embedding_pertanyaan

# --- Fungsi-fungsi untuk Q&A ---
def search_di_qdrant(client, pertanyaan, pdf_id, top_k=3):
    """Mencari di Qdrant (kode asli Anda)."""
    pertanyaan_embedding = embedding_question(pertanyaan)[0]
    hasil = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=pertanyaan_embedding.tolist(),
        query_filter=Filter(must=[FieldCondition(key="pdf_id", match=MatchValue(value=pdf_id))]),
        limit=top_k
    )
    return hasil

def generate_answer(context, pertanyaan):
    """Menghasilkan jawaban dengan SeaLLMs (kode asli Anda)."""
    conversation = [
        {"role": "system", "content": "Anda adalah asisten yang hanya menjawab berdasarkan teks konteks yang diberikan."},
        {"role": "user", "content": f"Berikut konteksnya:\n{context}\n\nPertanyaan: {pertanyaan}"}
    ]
    text = tokenizer_seallms.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer_seallms([text], return_tensors="pt").to(device)
    
    # TextStreamer bagus untuk melihat output secara real-time
    streamer = TextStreamer(tokenizer_seallms, skip_prompt=True, skip_special_tokens=True)
    generated_ids = model_seallms.generate(
        model_inputs.input_ids, max_new_tokens=512, streamer=streamer
    )
    
    # Dekode setelah selesai streaming
    response = tokenizer_seallms.batch_decode(
        [ids[len(model_inputs.input_ids[0]):] for ids in generated_ids],
        skip_special_tokens=True
    )[0]
    return response.strip()

def qdrant_answer(client, pertanyaan, pdf_id, bahasa_pdf):
    bahasa = detect(pertanyaan)
    # bahasa, _ = langid.classify(pertanyaan)
    print(bahasa)

    if bahasa != bahasa_pdf:
        if bahasa_pdf == "en":
            translate_pertanyaan = translate_idtoen(pertanyaan)
        if bahasa_pdf == "id":
            translate_pertanyaan = translate_entoid(pertanyaan)
    else:
        translate_pertanyaan = pertanyaan

    hasil_pencarian = search_di_qdrant(client, translate_pertanyaan, pdf_id, top_k=3)
    
    if not hasil_pencarian:
        print("Sistem search tidak berjalan dengan baik")
        return "Hasil tidak ada di dokumen", "", []
    
    top_k_payloads = [(h.payload['text'], h.score) for h in hasil_pencarian]
    gabungan_top3 = " ".join([h.payload['text'] for h in hasil_pencarian])
    skor_1 = hasil_pencarian[0].score
    
    print(f"Score tertinggi adalah {skor_1:.4f}")
    if skor_1 > 0.45: # Threshold
        print("\n--- Konteks Ditemukan ---")
        print(gabungan_top3)
        print("\n--- Menghasilkan Jawaban ---")
        jawaban = generate_answer(gabungan_top3, pertanyaan)
        return jawaban, gabungan_top3, [s for _, s in top_k_payloads]
    else:
        return "Hasil tidak ada di dokumen karena skor relevansi terlalu rendah", gabungan_top3, [s for _, s in top_k_payloads]


################################################################################
### BAGIAN 2: LLM AS A JUDGE
################################################################################

JUDGE_PROMPT_TEMPLATE = """
Anda adalah seorang juri AI yang objektif dan teliti. Tugas Anda adalah mengevaluasi kualitas jawaban yang dihasilkan oleh model AI lain berdasarkan pertanyaan dan konteks yang diberikan. Berikan evaluasi dalam format JSON yang valid.

Kriteria Evaluasi:
1.  **Kesesuaian (Faithfulness)**: Apakah jawaban sepenuhnya didasarkan pada informasi dari 'Konteks' dan relavan menjawab pertanyaan? Jawaban tidak boleh mengandung informasi eksternal atau halusinasi. Skor 1-5.

Berikut adalah data yang perlu dievaluasi:
---
[PERTANYAAN]: {question}
---
[KONTEKS]: {context}
---
[JAWABAN YANG DIHASILKAN]: {answer}
---

Sekarang, berikan evaluasi Anda. Ikuti format JSON di bawah ini tanpa tambahan teks atau penjelasan lain.

{{
  "faithfulness_score": [skor dari 1-5],
  "faithfulness_reasoning": "[penjelasan singkat mengapa Anda memberikan skor tersebut]",
  "corrected_answer": "[jika jawaban asli kurang ideal, berikan versi perbaikan singkat HANYA dari konteks]"
}}
"""

def evaluasi_dengan_llm_judge(question, context, answer):
    """Mengevaluasi output RAG menggunakan SeaLLMs sebagai juri."""
    print("\n" + "#"*50)
    print("### MEMULAI EVALUASI DENGAN LLM AS A JUDGE ###")
    print("#"*50)

    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, context=context, answer=answer)
    conversation = [{"role": "user", "content": prompt}]
    chat_prompt = tokenizer_seallms.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer_seallms(chat_prompt, return_tensors="pt").to(device)

    print("Judge sedang menganalisis...")
    outputs = model_seallms.generate(**inputs, max_new_tokens=512, do_sample=False)
    evaluation_text = tokenizer_seallms.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    
    print("\n--- Output Mentah dari Judge ---")
    print(evaluation_text)
    print("--- Akhir Output Mentah ---\n")
    
    try:
        json_match = evaluation_text[evaluation_text.find('{'):evaluation_text.rfind('}')+1]
        return json.loads(json_match)
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error: Gagal mem-parsing output JSON dari Judge. Error: {e}")
        return {"error": "Failed to parse JSON", "raw_output": evaluation_text}


################################################################################
### BAGIAN 3: EKSEKUSI UTAMA
################################################################################
def main():
    """Fungsi utama untuk menjalankan seluruh alur kerja."""
    pdf_id = "BPXx8DDUDJMWC-tbR11Y8lwqjZCpYUd3WyCb03jIsck"
    bahasa_pdf = "id"
    client = QdrantClient(host="127.0.0.1", port=6333)

    # 3. Ajukan pertanyaan ke sistem RAG
    pertanyaan = "Jelaskan mengenai reaksi kimia!"
    
    jawaban, gabungan_top3, scores = qdrant_answer(client, pertanyaan, pdf_id, bahasa_pdf)    

    # 4. Jika jawaban berhasil didapat, evaluasi dengan LLM Judge
    if gabungan_top3 and "tidak ada di dokumen" not in jawaban:
        evaluation = evaluasi_dengan_llm_judge(pertanyaan, gabungan_top3, jawaban)
        
        print("\n" + "="*25)
        print("HASIL EVALUASI FINAL")
        print("="*25)
        print(f"Pertanyaan: {pertanyaan}")
        print(f"Jawaban RAG: {jawaban}")
        print("-" * 25)
        
        if 'error' in evaluation:
            print(f"Evaluasi Gagal: {evaluation['error']}")
        else:
            print(f"Skor Kesesuaian: {evaluation.get('faithfulness_score', 'N/A')} - {evaluation.get('faithfulness_reasoning', 'N/A')}")
            print(f"Saran Perbaikan: {evaluation.get('corrected_answer', 'N/A')}")
        print("="*25)
    else:
        print("\nEvaluasi tidak dijalankan karena RAG gagal menemukan jawaban yang relevan.")


if __name__ == "__main__":
    main()
