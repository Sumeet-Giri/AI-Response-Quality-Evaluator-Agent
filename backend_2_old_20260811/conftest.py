"""
Test-time fakes for heavy ML / vector-DB dependencies.

This project's real dependencies (sentence-transformers' actual model
weights, a real ChromaDB index) are appropriate for running the app, but
downloading gigabytes of model weights just to verify that the
*application logic* (bucketing, weighting, RAG fallback wiring,
orchestration order, API contracts) is correct is unnecessary and slow.

This conftest.py installs deterministic, lightweight fakes for
`sentence_transformers` and `chromadb` into sys.modules *before* any
application code is imported by the test session. The fake embedding is a
bag-of-words average of per-word random unit vectors (seeded by a hash of
each word) — meaningfully different from a real transformer model, but
real enough that texts sharing words score higher cosine similarity than
texts that don't, which is what the agents' logic actually depends on.

This file only affects the test session (pytest auto-loads conftest.py).
It has zero effect on `uvicorn app.main:app` in normal use, which uses the
real packages declared in requirements.txt.
"""

import sys
import types
import hashlib

import numpy as np

_DIM = 384


def _word_vector(word: str) -> np.ndarray:
    seed = int.from_bytes(hashlib.sha256(word.encode()).digest()[:8], "little")
    rng = np.random.default_rng(seed)
    return rng.normal(size=_DIM)


def _pseudo_embed(text: str) -> np.ndarray:
    words = [w.strip(".,!?;:\"'()").lower() for w in str(text).split()]
    words = [w for w in words if w]
    if not words:
        return np.zeros(_DIM)
    vectors = np.array([_word_vector(w) for w in words])
    v = vectors.mean(axis=0)
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


class _FakeSentenceTransformer:
    def __init__(self, model_name_or_path=None, *args, **kwargs):
        self.model_name = model_name_or_path

    def encode(self, text_or_list, *args, **kwargs):
        if isinstance(text_or_list, (list, tuple)):
            return np.array([_pseudo_embed(t) for t in text_or_list])
        return _pseudo_embed(text_or_list)


_fake_st_module = types.ModuleType("sentence_transformers")
_fake_st_module.SentenceTransformer = _FakeSentenceTransformer
sys.modules["sentence_transformers"] = _fake_st_module


class _FakeCollection:
    def __init__(self):
        self._ids, self._docs, self._embeds, self._metas = [], [], [], []

    def add(self, ids, documents, embeddings, metadatas):
        self._ids.extend(ids)
        self._docs.extend(documents)
        self._embeds.extend(embeddings)
        self._metas.extend(metadatas)

    def count(self):
        return len(self._ids)

    def query(self, query_embeddings, n_results=3):
        if not self._embeds:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        q = np.asarray(query_embeddings[0], dtype=float)
        embeds = np.asarray(self._embeds, dtype=float)
        qn = q / (np.linalg.norm(q) + 1e-8)
        en = embeds / (np.linalg.norm(embeds, axis=1, keepdims=True) + 1e-8)
        sims = en @ qn
        order = np.argsort(-sims)[:n_results]
        return {
            "documents": [[self._docs[i] for i in order]],
            "metadatas": [[self._metas[i] for i in order]],
            "distances": [[float(1 - sims[i]) for i in order]],
        }


class _FakePersistentClient:
    def __init__(self, path=None):
        self._collections = {}

    def get_or_create_collection(self, name):
        return self._collections.setdefault(name, _FakeCollection())


_fake_chromadb_module = types.ModuleType("chromadb")
_fake_chromadb_module.PersistentClient = _FakePersistentClient
sys.modules["chromadb"] = _fake_chromadb_module
