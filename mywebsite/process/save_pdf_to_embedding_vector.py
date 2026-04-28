
import pdfplumber
from nltk.tokenize import sent_tokenize
import nltk
# nltk.download('punkt_tab')

from sentence_transformers import SentenceTransformer
# from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForQuestionAnswering
# from transformers import MarianMTModel, MarianTokenizer

# import faiss
import numpy as np
import torch
import fitz  # PyMuPDF
import re

import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue

# nltk.download('punkt')

# SETUP QDRANT
client = QdrantClient(host="127.0.0.1", port=6333)
collection_name = "pdf_embeddings"
vector_size = 384

# Buat collection jika belum ada
if collection_name not in [col.name for col in client.get_collections().collections]:
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )

# PROSES

# model_embedding = SentenceTransformer('all-MiniLM-L6-v2')
# model_embedding = SentenceTransformer('indobenchmark/indobert-base-p1')
model_embedding = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def detect_columns(blocks, tolerance=20):
    """Deteksi jumlah kolom berdasarkan posisi x0."""
    x_positions = sorted(set([round(b[0], 1) for b in blocks]))
    #kelompokkan posisi yang mirip (selisih kecil dianggap satu kolom)
    columns = []
    for x in x_positions:
        if not columns or abs(columns[-1] - x) > tolerance:
            columns.append(x)
    return columns

def extract_pdf_text(filepath):
    doc = fitz.open(filepath)
    all_text = ""

    for page in doc:
        blocks = page.get_text("blocks")
        if not blocks:
            continue

        #deteksi kolom dengan batas kanan
        columns_x = detect_columns(blocks)
        columns_x.append(page.rect.width) 

        #looping tiap kolom berdasarkan deteksi otomatis
        for col_idx in range(len(columns_x) - 1):
            x0 = columns_x[col_idx]
            x1 = columns_x[col_idx + 1]
            col_rect = fitz.Rect(x0, 0, x1, page.rect.height)

            col_blocks = page.get_text("blocks", clip=col_rect)
            col_blocks = sorted(col_blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))

            for b in col_blocks:
                text = b[4].strip()
                if text:
                    text = re.sub(r"\n+", " ", text)
                    all_text += text + " "
            all_text += " " 

        #pindah antar halaman
        all_text += " "  

    return all_text

# def extract_pdf_text(filepath):
#     text = ""

#     with pdfplumber.open(filepath) as pdf:
#         for page in pdf.pages:
#             text += page.extract_text() + "\n"\
            
#     return text

def proses_chunk(kalimat_teks, ukuranchunk=3, kalimatchunk=1):
    # chunk_size = 4
    # chunks = [" ".join(kalikalimat_teksmat[i:i+chunk_size]) for i in range(0, len(kalimat_teks), chunk_size)]

    chunk_size = ukuranchunk
    stride = kalimatchunk
    chunks = [
        " ".join(kalimat_teks[i:i+chunk_size]) 
        for i in range(0, len(kalimat_teks) - chunk_size + 1, stride)
    ]

    return chunks

def embedder_file(kalimat):
    embeddings = model_embedding.encode(kalimat, normalize_embeddings=True)
    # print(embeddings.shape) # Harus (jumlah kalimat, ukuran vektor)    
    return embeddings

def simpan_ke_qdrant(embedding, teks, pdf_id):
    points = []
    for i, vector in enumerate(embedding):
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector.tolist(),
            payload={
                "text": teks[i],
                # "user_id": user_id,
                "pdf_id": pdf_id
            }
        ))
    client.upsert(collection_name=collection_name, points=points)


# JALANKAN SIMPAN PDF EMBEDDING
def proses_dan_simpan_ke_qdrant(filepath, pdf_id):
    try:
        kalimatjoin = extract_pdf_text(filepath)
        # print(kalimatjoin)

        #Tokenize file pdf
        kalimat = sent_tokenize(kalimatjoin, language="english")
        # print(kalimat)

        chunks = proses_chunk(kalimat_teks=kalimat, ukuranchunk=4, kalimatchunk=2)

        # Embedding file pdf dengan sentence transformer dan simpan embedding yang dilakukan
        hasil_embedding_per_kalimat = embedder_file(chunks)

        simpan_ke_qdrant(hasil_embedding_per_kalimat, chunks, pdf_id)
        # print("Data berhasil disimpan ke Qdrant.")

        return True
    except Exception as e:
        print("Gagal dikarenakan = ", e)
        return False