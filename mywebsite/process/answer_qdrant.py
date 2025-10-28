import nltk

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForQuestionAnswering, AutoModelForCausalLM
from transformers import MarianMTModel, MarianTokenizer, pipeline
from transformers import TextStreamer

# import faiss
import numpy as np
import torch

# untuk menentukan bahasa
# import langid #lagid kurang cocok untuk translate karena bahasa yang dihasilkan untuk kalimat pendek cenderung salah
from langdetect import detect

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct, Filter, FieldCondition, MatchValue


client = QdrantClient(host="127.0.0.1", port=6333)
collection_name = "pdf_embeddings"
vector_size = 384

model_embedding = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

def validasi_pertanyaan(pertanyaan, bahasa):
    def fungsitanya(kata_tanya):
        pertanyaan_lower = pertanyaan.lower().split()
        jumlah_kata_tanya = 0
        for kata in kata_tanya:
            if kata in pertanyaan_lower:
                jumlah_kata_tanya +=1

        if jumlah_kata_tanya > 1:
            print(pertanyaan)
            print("Error: Pertanyaan mengandung lebih dari satu kata tanya.")
            return "Maaf, pertanyaan hanya boleh mengandung satu kata tanya utama.", None, None
        
        return None
    
    if bahasa == "id":
        kata_tanya = ["apa", "siapa", "mengapa", "bagaimana", "kapan", "dimana", "berapakah", "berapa"]
        return fungsitanya(kata_tanya)
    elif bahasa == "en":
        kata_tanya = ["what", "who", "why", "how", "when", "where", "which", "how many", "how much"]
        return fungsitanya(kata_tanya)
    else:
        return "Error: Bahasa pertanyaan tidak dikenali atau format tidak didukung.", None, None
    

def embedding_question(pertanyaan):
    embedding_pertanyaan = model_embedding.encode([pertanyaan], normalize_embeddings=True)
    return embedding_pertanyaan

def search_di_qdrant(pertanyaan, pdf_id, top_k):
    # 1. Embedding pertanyaan
    pertanyaan_embedding = embedding_question(pertanyaan)[0]  # ambil array 1D
    
    # 2. Query ke Qdrant berdasarkan user_id dan pdf_id
    hasil = client.search(
        collection_name=collection_name,
        query_vector=pertanyaan_embedding.tolist(),
        query_filter=Filter(
            must=[
                # FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                FieldCondition(key="pdf_id", match=MatchValue(value=pdf_id)),
            ]
        ),
        limit=top_k
    )

    return hasil

# yang sudah dicoba:
# google/flat-t5-large
# google/flat-t5-small -> memberian jawaban yang tidak sesuai konteks, mungkin karena flat yang bersifat small
# deepset/bert-base-cased-squad2 -> tidak cocok karena qa bahasa inggris
# indobenchmark/indobert-base-p1 -> tidak disediakan untuk qa
# adirizq/indonesian-end2end-qag-flan-t5 -> tidak untuk menjawab pertanyaan (qa)
# deepset/xlm-roberta-base-squad2 


# qa_pipeline = pipeline("question-answering", model="deepset/xlm-roberta-base-squad2")

# tokenizer_qa = AutoTokenizer.from_pretrained("google/flan-t5-large")
# model_qa = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")

# "teknium/OpenHermes-2.5-Mistral-7B" = mistral bisa tetapi harus menggunakan GPU dan terlalu berat 7B

device = "cpu"
tokenizer_seallms = AutoTokenizer.from_pretrained("SeaLLMs/SeaLLMs-v3-1.5B-Chat")
model_seallms = AutoModelForCausalLM.from_pretrained(
    "SeaLLMs/SeaLLMs-v3-1.5B-Chat",
    torch_dtype=torch.bfloat16,  # hemat memori
    device_map="auto"  # otomatis ke GPU/CPU sesuai device
)

def generate_answer(context, pertanyaan):
    # ---------------- jawab berdasarkan qa_pipeline --------------------------
    # input_text = f"Jawablah pertanyaan berikut berdasarkan konteks.\n\nquestion: {pertanyaan}\ncontext: {context}\njawaban:"
    # inputs = tokenizer_qa(input_text, return_tensors="pt", truncation=True)
    
    # with torch.no_grad():
    #     outputs = model_qa.generate(**inputs, max_length=1000)

    # return tokenizer_qa.decode(outputs[0], skip_special_tokens=True)


    # ---------------- jawab berdasarkan tokenizer_qa dan model_qa --------------------------
    # result = qa_pipeline(question=pertanyaan, context=context)
    # return result['answer']


    # ---------------- jawab berdasarkan tokenizer_seallms dan model_seallms --------------------------
    conversation = [
        {
            "role": "system",
            "content": "Anda adalah asisten yang hanya menjawab berdasarkan teks konteks yang diberikan."
        },
        {
            "role": "user",
            "content": f"Berikut konteksnya:\n{context}\n\nPertanyaan: {pertanyaan}"
        }
    ]

    text = tokenizer_seallms.apply_chat_template(conversation, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer_seallms([text], return_tensors="pt").to(device)

    streamer = TextStreamer(tokenizer_seallms, skip_prompt=True, skip_special_tokens=True)
    generated_ids = model_seallms.generate(model_inputs.input_ids, max_new_tokens=512, streamer=streamer)
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer_seallms.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return response

tokenizer_translate_entoid = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-id")
model_translate_entoid = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-en-id")

tokenizer_translate_idtoen = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-id-en")
model_translate_idtoen = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-id-en")

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


def qdrant_answer(pertanyaan, pdf_id, bahasa_pdf):
    bahasa = detect(pertanyaan)
    # bahasa, _ = langid.classify(pertanyaan)
    print(bahasa)
    
    cek_bahasa = validasi_pertanyaan(pertanyaan, bahasa)
    if cek_bahasa:
        return cek_bahasa, None, None

    if bahasa != bahasa_pdf:
        if bahasa_pdf == "en":
            translate_pertanyaan = translate_idtoen(pertanyaan)
        if bahasa_pdf == "id":
            translate_pertanyaan = translate_entoid(pertanyaan)
    else:
        translate_pertanyaan = pertanyaan

    hasil_pencarian = search_di_qdrant(translate_pertanyaan, pdf_id, top_k=3)

    if not hasil_pencarian:
        print("Sistem search tidak berjalan dengan baik")
        return "hasil tidak ada di dokumen", None, None
    else:
        print("\n--- Hasil ---")

        top_k = [(h.payload['text'], h.score) for h in hasil_pencarian]
        gabungan_top3 = " ".join([h.payload['text'] for h in hasil_pencarian])

        skor_1 = hasil_pencarian[0].score
        print(f"score tertinggi adalah {skor_1}")

        if skor_1 > 0.45:
            jawaban = generate_answer(gabungan_top3, translate_pertanyaan)
            
            if bahasa != bahasa_pdf:
                if (bahasa == "id" and bahasa_pdf == "en"):
                    translate_jawaban = translate_entoid(jawaban)
                if (bahasa == "en" and bahasa_pdf == "id"):
                    translate_jawaban = translate_idtoen(jawaban)
            else:
                translate_jawaban = jawaban

            print(f"Pertanyaan: {pertanyaan}")
            print(f"Jawaban: {translate_jawaban}")
            print(f"Kalimat Asli: {gabungan_top3}")

            return translate_jawaban, gabungan_top3, top_k
        else:
            print("Hasil tidak ada di dokumen!")
            return "hasil tidak ada di dokumen", None, None