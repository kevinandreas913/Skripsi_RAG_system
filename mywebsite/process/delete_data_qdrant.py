from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import json

def delete_qdrant_data(pdf_id):
    client = QdrantClient(host="127.0.0.1", port=6333)
    collection_name = "pdf_embeddings"

    try:
        # Hapus semua vector dengan payload api_key tertentu
        client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="pdf_id",
                        match=MatchValue(value=pdf_id)
                    ),
                ]
            )
        )
        print("Data di qdrant berhasil dihapus.")
    except Exception as e:
        print("Gagal menghapus data di qdrant database.")