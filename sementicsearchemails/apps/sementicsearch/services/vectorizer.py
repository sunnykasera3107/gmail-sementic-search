import os
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()
_model = None

def laod_model():
    global _model
    print("Running startup code...")
    _model = SentenceTransformer(os.getenv('VECTORIZER_MODEL'))

def get_model():
    return _model


class Vectorization:
    ''' Performs vectorization of content and feature find user query
    '''
    def __init__(self, user):
        self._user = user
        self._st = get_model()
        os.makedirs("data/vectorized", exist_ok=True)
        self._chroma_client = chromadb.PersistentClient(path="data/chroma_db")

    def transform(self, data):
        return self._st.encode(data)
    
    def vectorize_raw_data(self, data):
        try:
            collection = self._chroma_client.get_or_create_collection(name=f"{self._user.id}-st-gmail")
            collection.upsert(**data)
        except Exception as e:
            raise Exception(f"Try again a few second later. If fails again, send screenshot of this to admin {str(e)}")
        
    def _get_all_records(self):
        collection = self._chroma_client.get_or_create_collection(name=f"{self._user.id}-st-gmail")
        if collection.count() == 0:
            return None
        return [id.split("-")[0] for id in collection.get()['ids']]

    def find_data(self, data: str | None = None):
        collection = self._chroma_client.get_or_create_collection(name=f"{self._user.id}-st-gmail")
        print("Collection counts: ", collection.count())
        if collection.count() == 0:
            return None
        
        results = []
        if data is None:
            query_result = collection.get()
            query_result['ids'] = [query_result['ids']]
            query_result['documents'] = [query_result['documents']]
        else:
            embedded = self.transform(data)
            query_result = collection.query(
                query_embeddings=[embedded],
                n_results=10
            )

        for r in range(len(query_result['ids'][0])):
            if 'distances' in query_result and (query_result['distances'][0][r] - 1) <= 0.50:
                continue

            id = query_result['ids'][0][r].split("-")
            results.append(
                {
                    "id": query_result['ids'][0][r],
                    "link": f"https://mail.google.com/mail/u/0/#all/{id[-1]}",
                    "content": f"{query_result['documents'][0][r][:120]}..."
                }
            )
        
    
        return results