import re
from typing import Any, Dict, List


def clean_text(text: str) -> str:
    """Cleans transcript text by removing bracketed noises ([Music], [Applause]) and normalizing whitespace."""
    if not text:
        return ""
    # Remove bracketed cues like [Music], [Laughter], [Applause], (cheers), etc.
    cleaned = re.sub(r"\[.*?\]|\(.*?\)", " ", text)
    # Remove HTML entities like &amp;, &#39;, etc.
    cleaned = re.sub(r"&[a-zA-Z0-9#]+;", " ", cleaned)
    # Normalize excessive whitespace and linebreaks
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def chunk_transcript(
    snippets: List[Dict[str, Any]],
    min_words: int = 80,
    max_words: int = 150,
) -> List[Dict[str, Any]]:
    """
    Groups raw transcript snippets into timestamp-aware chunks of 80–150 words.

    Each output chunk dict contains:
        - chunk_index: int (0-indexed order)
        - start_time: float (seconds)
        - end_time: float (seconds)
        - text: str (cleaned chunk text)
        - word_count: int
    """
    if not snippets:
        return []

    chunks: List[Dict[str, Any]] = []
    current_words: List[str] = []
    current_start: float = 0.0
    current_end: float = 0.0
    chunk_index = 0

    for i, snippet in enumerate(snippets):
        raw_text = snippet.get("text", "")
        cleaned_snippet = clean_text(raw_text)
        if not cleaned_snippet:
            continue

        words = cleaned_snippet.split()
        snippet_start = float(snippet.get("start", 0.0))
        snippet_dur = float(snippet.get("duration", 0.0))
        snippet_end = snippet_start + snippet_dur

        if not current_words:
            # First snippet in chunk
            current_start = snippet_start
            current_end = snippet_end
            current_words.extend(words)
        else:
            current_words.extend(words)
            current_end = max(current_end, snippet_end)

        # Check if we reached the word target
        if len(current_words) >= min_words:
            # Check sentence ending boundary (., !, ?) or if exceeding max_words
            ends_with_punctuation = bool(re.search(r"[.!?]$", cleaned_snippet))
            if ends_with_punctuation or len(current_words) >= max_words or i == len(snippets) - 1:
                chunk_text = " ".join(current_words)
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "start_time": round(current_start, 2),
                        "end_time": round(current_end, 2),
                        "text": chunk_text,
                        "word_count": len(current_words),
                    }
                )
                chunk_index += 1
                current_words = []
                current_start = 0.0
                current_end = 0.0

    # Flush any remaining words as final chunk
    if current_words:
        chunks.append(
            {
                "chunk_index": chunk_index,
                "start_time": round(current_start, 2),
                "end_time": round(current_end, 2),
                "text": " ".join(current_words),
                "word_count": len(current_words),
            }
        )

    return chunks
