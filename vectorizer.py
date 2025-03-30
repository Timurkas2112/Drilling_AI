from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

model = SentenceTransformer('cointegrated/rubert-tiny2')

df = pd.read_csv('data/tables_with_descrp.csv')
documents = df.description.to_list()

loaded_embeddings = np.load('data/document_embeddings.npy')
faiss.normalize_L2(loaded_embeddings)

dimension = loaded_embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(loaded_embeddings)

def semantic_search(query, top_k=20):
    query_embedding = model.encode([query], convert_to_tensor=True)
    query_np = query_embedding.cpu().numpy()
    faiss.normalize_L2(query_np)

    distances, indices = index.search(query_np, top_k)

    # results = []
    # for i in range(top_k):
    #     results.append({
    #         "index": indices[0][i],
    #         "document": documents[indices[0][i]],
    #         "score": distances[0][i]
    #     })
    results = []
    for i in range(top_k):
        results.append(df.iloc[int(indices[0][i])].tables)
    return results

# query = "Какие бригады работают в скважине №20?"
# results = semantic_search(query)

# print(f"Результаты для '{query}':")
# for i, res in enumerate(results, 1):

#     print(f"{i}. [Индекс: {res['index']}] {res['document']} (сходство: {res['score']:.4f})")

