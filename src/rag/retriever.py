import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from .knowledge_base import DOCUMENTS

# Store ChromaDB in the models directory
CHROMA_DIR = Path(__file__).parent.parent.parent / "models" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Use sentence-transformers for embeddings — free, local, no API needed
# all-MiniLM-L6-v2 is small (80MB), fast, and good enough for this task
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_or_create_collection() -> chromadb.Collection:
    """
    Get the ChromaDB collection, creating and populating it
    if it doesn't exist yet.

    ChromaDB is a local vector database — it stores document
    embeddings on disk and lets you search by semantic similarity.

    The embedding function converts text to a 384-dimensional
    vector. Similar concepts end up near each other in this
    vector space, so searching for "momentum indicator" returns
    documents about MACD and RSI even if they don't contain
    those exact words.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    collection = client.get_or_create_collection(
        name              = "investiq_knowledge",
        embedding_function= embedding_fn,
        metadata          = {"description": "InvestIQ investing knowledge base"}
    )

    # If collection is empty, populate it
    if collection.count() == 0:
        print("Populating knowledge base (first time only)...")
        _populate_collection(collection)
        print(f"  Added {collection.count()} documents to knowledge base.")
    else:
        print(f"Knowledge base loaded: {collection.count()} documents.")

    return collection


def _populate_collection(collection: chromadb.Collection):
    """
    Add all documents to the ChromaDB collection.
    Each document is split into chunks for better retrieval.
    """
    ids       = []
    documents = []
    metadatas = []

    for doc in DOCUMENTS:
        # Split long documents into paragraphs for better retrieval
        # A query about "RSI overbought" should return the specific
        # paragraph about that, not the entire RSI document
        paragraphs = [p.strip() for p in doc["content"].split("\n\n")
                      if p.strip()]

        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) < 50:
                continue  # skip very short paragraphs

            chunk_id = f"{doc['id']}_chunk_{i}"
            ids.append(chunk_id)
            documents.append(paragraph)
            metadatas.append({
                "doc_id"  : doc["id"],
                "topic"   : doc["topic"],
                "title"   : doc["title"],
                "chunk_idx": i
            })

    collection.add(
        ids       = ids,
        documents = documents,
        metadatas = metadatas
    )


def retrieve(
    query     : str,
    n_results : int = 3,
    topic_filter: str = None
) -> list:
    """
    Retrieve the most relevant knowledge base chunks for a query.

    Args:
        query        : the user's question in natural language
        n_results    : number of chunks to retrieve (3 is usually enough)
        topic_filter : optional — restrict to one topic (e.g. "RSI")

    Returns:
        List of dicts with keys: content, topic, title, distance
        Sorted by relevance (most relevant first)
    """
    collection = get_or_create_collection()

    where = {"topic": topic_filter} if topic_filter else None

    results = collection.query(
        query_texts = [query],
        n_results   = min(n_results, collection.count()),
        where       = where
    )

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "content" : results["documents"][0][i],
            "topic"   : results["metadatas"][0][i]["topic"],
            "title"   : results["metadatas"][0][i]["title"],
            "distance": results["distances"][0][i]
            # Lower distance = more similar = more relevant
        })

    return chunks


def get_context_for_query(query: str, n_results: int = 3) -> str:
    """
    Retrieve relevant chunks and format them as a context string
    for injection into the LLM prompt.

    Returns a formatted string like:
    [Source: Moving Averages]
    The SMA50 captures the medium-term trend...

    [Source: MACD]
    The MACD histogram shows whether momentum...
    """
    chunks = retrieve(query, n_results=n_results)

    if not chunks:
        return "No relevant context found."

    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"[Source: {chunk['title']}]\n{chunk['content']}"
        )

    return "\n\n".join(context_parts)


def reset_knowledge_base():
    """
    Delete and recreate the knowledge base.
    Use this when you add new documents to knowledge_base.py.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection("investiq_knowledge")
        print("Knowledge base deleted.")
    except Exception:
        pass
    get_or_create_collection()
    print("Knowledge base recreated.")