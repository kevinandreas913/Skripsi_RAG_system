import os
import time
import joblib
import numpy as np
import tensorflow as tf
from transformers import TFBertModel, BertTokenizer

# --------------------------------------Konfigurasi------------------------------- 
ARTIFACTS_DIR = "mywebsite/process/bert_lg_artifacts"
MODEL_NAME = "bert-base-multilingual-cased"
MAX_LEN = 128

# Muat tokenizer & BERT
tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
bert_model = TFBertModel.from_pretrained(MODEL_NAME, from_pt=True)

#model Logistic Regression
logreg_path = os.path.join(ARTIFACTS_DIR, "logreg_model.joblib")
logreg_model = joblib.load(logreg_path)

# --------------------------------------Prediksi------------------------------- 
def predict_single_text(text_to_predict, tokenizer, bert_model, logreg_model):
    print(f"Analyzing text: '{text_to_predict}'...")
    start_time = time.time()

    #embedding dari input
    inputs = tokenizer(
        [text_to_predict],
        padding=True,
        truncation=True,
        max_length=MAX_LEN,
        return_tensors="tf"
    )
    outputs = bert_model(inputs)
    embedding = outputs.last_hidden_state[:, 0, :].numpy().astype("float32")

    #prediksi dengan Logistic Regression
    predicted_label = logreg_model.predict(embedding)[0]
    probas = logreg_model.predict_proba(embedding)[0]
    confidence = np.max(probas)

    if predicted_label == "0":
        keterangan = "success"
    else:
        keterangan = "gagal"

    end_time = time.time()

    #hasil
    print("\n" + "="*20 + " ANALYSIS RESULT " + "="*20)
    print(f"Predicted Class: Label = {predicted_label}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Probabilities: {probas}")
    print(f"Inference Time: {end_time - start_time:.4f} seconds")
    print("=" * 57)

    return predicted_label, keterangan

def mainhatespeechdetection(inputtext):
    print("Proses dimulai")
    try:
        print("Berhasil menjalankan model dan tokenizer")
        print("-" * 57)

        # Teks yang ingin dideteksi
        input_text = inputtext

        predicted_label, keterangan = predict_single_text(input_text, tokenizer, bert_model, logreg_model)

        return predicted_label, keterangan
    
    except FileNotFoundError as e:
        print("File tidak ditemukan")
        return None, "file tidak ditemukan"
    except Exception as e:
        print(f"Error dikarenakan: {e}")
        return None, f"error: {e}"