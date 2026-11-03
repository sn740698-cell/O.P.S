import os
import sys
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "ops-temporary-rag")
CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
REGION = os.environ.get("PINECONE_REGION", "us-east-1")
DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "768"))

print(f"Testing Pinecone connectivity with index: {INDEX_NAME}, dimension: {DIMENSION}")

from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=API_KEY)

# 1. List existing indexes
existing_indexes = [idx.name for idx in pc.list_indexes()]
print(f"Existing indexes: {existing_indexes}")

if INDEX_NAME not in existing_indexes:
    print(f"Creating serverless index '{INDEX_NAME}' with dim={DIMENSION}, metric='cosine'...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=CLOUD,
            region=REGION
        )
    )
    print("Waiting for index to become ready...")
    while not pc.describe_index(INDEX_NAME).status['ready']:
        time.sleep(2)
        print(".", end="", flush=True)
    print("\nIndex is READY!")
else:
    desc = pc.describe_index(INDEX_NAME)
    print(f"Index exists: dim={desc.dimension}, metric={desc.metric}, status={desc.status['ready']}")
    assert desc.dimension == DIMENSION, f"Index dimension {desc.dimension} != expected {DIMENSION}"

# 2. Test connection to index
index = pc.Index(INDEX_NAME)
stats = index.describe_index_stats()
print(f"Index stats: total_vector_count={stats.total_vector_count}")

# 3. Test upsert in a temporary test namespace
test_namespace = "ops-rag-test-verification"
dummy_vector = [0.01 * (i % 10) for i in range(DIMENSION)]
test_id = "test-doc-1-chunk-0"

print(f"Upserting test vector into namespace '{test_namespace}'...")
index.upsert(
    vectors=[
        {
            "id": test_id,
            "values": dummy_vector,
            "metadata": {"doc_id": "test-doc-1", "chunk_id": "0", "page": 1}
        }
    ],
    namespace=test_namespace
)

# Wait briefly for indexing consistency
time.sleep(2)

# 4. Test vector retrieval / query
print(f"Querying test vector in namespace '{test_namespace}'...")
query_res = index.query(
    vector=dummy_vector,
    top_k=1,
    include_metadata=True,
    namespace=test_namespace
)
print(f"Query matches found: {len(query_res.matches)}")
assert len(query_res.matches) > 0, "No matches returned!"
print(f"Top match ID: {query_res.matches[0].id}, score: {query_res.matches[0].score}")

# 5. Test namespace deletion / clear
print(f"Testing deletion of namespace '{test_namespace}'...")
index.delete(delete_all=True, namespace=test_namespace)
time.sleep(2)

# Verify deletion
stats_after = index.describe_index_stats()
namespaces = stats_after.namespaces or {}
print(f"Namespaces after delete: {namespaces.keys()}")
assert test_namespace not in namespaces or namespaces[test_namespace].vector_count == 0, "Namespace was not cleared!"

print("\nSUCCESS: All Pinecone lifecycle operations verified successfully!")
