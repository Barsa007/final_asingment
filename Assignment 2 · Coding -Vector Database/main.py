import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import heroes


ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

client = chromadb.Client()
collection = client.create_collection(
    name="super_heros",
    embedding_function=ef
)

collection.add(
    documents=[hero["document"] for hero in heroes.heroes],
    metadatas = [hero["metadata"] for hero in heroes.heroes],
    ids = [hero["id"] for hero in heroes.heroes]
)

print(f"Collection created with {collection.count()} documents")

queries = [
    "a hero who defeats stronger enemies through intelligence and careful planning",

    "someone who can survive almost any injury and jokes during dangerous situations",

    "a protector who inspires hope and always chooses justice over personal gain",

    "a powerful warrior connected to ancient magic and supernatural forces",

    "a ruler who protects an advanced hidden nation using both tradition and cutting-edge technology"
]

for query in queries:
    results = collection.query(
        query_texts=[query],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    print(f"\n🔍 Query: '{query}'")
    print("-" * 60)
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        print(f"  Distance: {dist:.4f}  |  {doc[:80]}...")
        print(f"  Metadata: {meta}")


