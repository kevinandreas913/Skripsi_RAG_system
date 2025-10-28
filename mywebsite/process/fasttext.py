# import fitz  # PyMuPDF
# import re

# def extract_multicolumn_pdf(pdf_path, num_columns=2):
#     doc = fitz.open(pdf_path)
#     all_text = ""

#     for page in doc:
#         width = page.rect.width
#         col_width = width / num_columns

#         # Ambil teks per kolom, dari kiri ke kanan
#         for col in range(num_columns):
#             x0 = col * col_width
#             x1 = (col + 1) * col_width
#             col_rect = fitz.Rect(x0, 0, x1, page.rect.height)

#             # Ambil blok teks di kolom ini
#             blocks = page.get_text("blocks", clip=col_rect)
#             blocks = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))

#             for b in blocks:
#                 text = b[4].strip()
#                 if text:
#                     # Gabung baris yang terputus
#                     text = re.sub(r"\n+", " ", text)  # hilangkan line break dalam paragraf
#                     all_text += text + " "  # double newline untuk paragraf

#         all_text += "\n"

#     return all_text.strip()

# pdf_path = r"D:\Skripsi\Django\andreasproject\mywebsite\process\kolom.pdf"
# hasil_teks = extract_multicolumn_pdf(pdf_path, num_columns=2)

# # Simpan hasil ke file teks
# with open("hasil_rapi.txt", "w", encoding="utf-8") as f:
#     f.write(hasil_teks)

import fitz  # PyMuPDF
import re
import numpy as np

def detect_columns(blocks, tolerance=20):
    """Deteksi jumlah kolom berdasarkan posisi x0."""
    x_positions = sorted(set([round(b[0], 1) for b in blocks]))
    # Kelompokkan posisi yang mirip (selisih kecil dianggap satu kolom)
    columns = []
    for x in x_positions:
        if not columns or abs(columns[-1] - x) > tolerance:
            columns.append(x)
    return columns

def extract_multicolumn_pdf_auto(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""

    for page in doc:
        blocks = page.get_text("blocks")
        if not blocks:
            continue

        # Deteksi kolom
        columns_x = detect_columns(blocks)
        columns_x.append(page.rect.width)  # batas kanan

        # Loop tiap kolom berdasarkan deteksi otomatis
        for col_idx in range(len(columns_x) - 1):
            x0 = columns_x[col_idx]
            x1 = columns_x[col_idx + 1]
            col_rect = fitz.Rect(x0, 0, x1, page.rect.height)

            col_blocks = page.get_text("blocks", clip=col_rect)
            col_blocks = sorted(col_blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))

            for b in col_blocks:
                text = b[4].strip()
                if text:
                    # Hapus line break dalam paragraf
                    text = re.sub(r"\n+", " ", text)
                    all_text += text + " "
            all_text += " "  # pindah antar kolom

        all_text += " "  # pindah antar halaman

    return all_text

# --- Contoh pemakaian ---
pdf_path = r"D:\Skripsi\Django\andreasproject\mywebsite\process\kolom2.pdf"
hasil_teks = extract_multicolumn_pdf_auto(pdf_path)

# Simpan ke file teks
with open("hasil_rapi_auto.txt", "w", encoding="utf-8") as f:
    f.write(hasil_teks)
