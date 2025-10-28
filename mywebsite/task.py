from .process.save_pdf_to_embedding_vector import proses_dan_simpan_ke_qdrant
import time

def proses_pdf_task(file_path, pdf_id):
    """
    Task untuk memproses PDF dan menyimpan chunk ke Qdrant.
    Dipanggil oleh worker Django-Q, bukan langsung di view.
    """
    
    print(f"[TASK] Mulai memproses PDF {pdf_id} dari {file_path}")
    
    try:
        proses_dan_simpan_ke_qdrant(file_path, pdf_id)
        print(f"[TASK] Selesai memproses PDF {pdf_id}")
        return {"status": "success", "pdf_id": pdf_id}
    except Exception as e:
        print(f"[TASK] Gagal memproses PDF {pdf_id}: {e}")
        return {"status": "error", "pdf_id": pdf_id, "error": str(e)}
