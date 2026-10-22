"""
IMPACT LAB - NLP & Solution Discovery Engine
Problem-to-Impact Platform
=============================================
Provides:
1. Text Normalization & Tokenization
2. Stop-word Removal (Standard English corpus)
3. Keyword Extraction (TF-IDF & Frequency weighted)
4. Vector Space Modeling (TF-IDF Vectorizer)
5. Cosine Similarity Calculation
6. Hybrid Relevance Ranking (TF-IDF + Keyword Overlap)
7. Match Explainability (Common keywords & human-readable rationale)

Designed to be transparent, mathematically rigorous, and fully explainable.
"""

import re
import math
from collections import Counter

# Standard English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when",
    "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves", "also", "need", "needs", "want", "wants", "like"
}


def tokenize(text):
    """
    Normalizes input text: converts to lowercase, strips punctuation,
    and returns a list of clean tokens with length >= 2.
    """
    if not text:
        return []
    clean_text = re.sub(r"[^\w\s-]", " ", text.lower())
    clean_text = re.sub(r"[-_]", " ", clean_text)
    tokens = clean_text.split()
    return [t for t in tokens if len(t) >= 2]


def stem(word):
    """
    Rule-based morphological normalizer for English word roots.
    Handles plurals, common suffixes (-ing, -ed, -tion, -ment, -al).
    """
    w = word.lower()
    if len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    if w.endswith("tion") and len(w) > 5:
        return w[:-4]
    if w.endswith("ment") and len(w) > 6:
        return w[:-4]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def remove_stopwords(tokens):
    """Filters out common grammatical stop words."""
    return [t for t in tokens if t not in STOP_WORDS and not t.isdigit()]


def extract_keywords(text, top_n=8):
    """
    Extracts top N meaningful keywords based on token frequency and length.
    """
    tokens = remove_stopwords(tokenize(text))
    if not tokens:
        return []
    counter = Counter(tokens)
    # Prefer tokens that are descriptive (longer words slightly prioritized)
    scored = sorted(
        counter.items(),
        key=lambda item: (item[1] * (1.0 + 0.1 * min(len(item[0]), 10))),
        reverse=True
    )
    return [word for word, count in scored[:top_n]]


class TextVectorizer:
    """
    Computes Term Frequency - Inverse Document Frequency (TF-IDF) vectors
    and calculates Cosine Similarity between documents.
    """
    def __init__(self, documents):
        """
        Initializes vocabulary and IDF tables from a corpus of documents.
        documents: list of strings
        """
        self.doc_count = len(documents)
        self.tokenized_docs = [remove_stopwords(tokenize(d)) for d in documents]
        
        # Build vocabulary and Document Frequency (DF)
        self.df = Counter()
        for doc_tokens in self.tokenized_docs:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                self.df[token] += 1
                
        # Calculate smooth IDF: ln((1 + N) / (1 + DF)) + 1
        self.idf = {}
        for token, freq in self.df.items():
            self.idf[token] = math.log((1 + self.doc_count) / (1 + freq)) + 1.0

    def transform(self, text):
        """
        Converts a text string into a normalized TF-IDF vector dict.
        """
        tokens = remove_stopwords(tokenize(text))
        if not tokens:
            return {}
        
        tf = Counter(tokens)
        total_tokens = len(tokens)
        
        vector = {}
        squared_sum = 0.0
        
        for token, count in tf.items():
            # Standard term frequency
            term_freq = count / total_tokens
            # Smooth IDF for known words; default smooth baseline for unseen words
            idf_val = self.idf.get(token, math.log(1 + self.doc_count) + 1.0)
            weight = term_freq * idf_val
            vector[token] = weight
            squared_sum += weight * weight
            
        # L2 Vector Normalization
        norm = math.sqrt(squared_sum)
        if norm > 0:
            for token in vector:
                vector[token] /= norm
                
        return vector

    @staticmethod
    def cosine_similarity(vec_a, vec_b):
        """
        Computes dot product of two L2-normalized vectors.
        Returns value between 0.0 (orthogonal) and 1.0 (identical direction).
        """
        if not vec_a or not vec_b:
            return 0.0
        
        # Iterate over the smaller vector for computational efficiency
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
            
        dot_product = sum(weight * vec_b.get(term, 0.0) for term, weight in vec_a.items())
        return min(max(dot_product, 0.0), 1.0)


def rank_matching_solutions(query_text, candidate_solutions, min_score_threshold=0.08):
    """
    Ranks solutions by comparing query_text (problem title + description + keywords)
    against candidate solution records.

    candidate_solutions: list of dicts with keys:
      'id', 'title', 'description', 'category', 'required_resources',
      'difficulty', 'expected_benefit', 'status', 'problem_title' (optional)

    Returns:
      ranked_matches: list of match dicts with relevance scores, matched keywords,
      and explainable recommendation strings.
    """
    if not query_text or not candidate_solutions:
        return []

    # 1. Build corpus for TF-IDF training
    solution_docs = []
    for sol in candidate_solutions:
        doc = f"{sol.get('title', '')} {sol.get('description', '')} {sol.get('category', '')} {sol.get('required_resources', '')} {sol.get('expected_benefit', '')} {sol.get('problem_title', '')} {sol.get('problem_keywords', '')}"
        solution_docs.append(doc)

    corpus = [query_text] + solution_docs
    vectorizer = TextVectorizer(corpus)

    query_vector = vectorizer.transform(query_text)
    query_keywords = set(extract_keywords(query_text, top_n=15))

    ranked_results = []

    for i, sol in enumerate(candidate_solutions):
        sol_doc = solution_docs[i]
        sol_vector = vectorizer.transform(sol_doc)
        
        # 1. Cosine similarity from TF-IDF vectors
        cos_sim = vectorizer.cosine_similarity(query_vector, sol_vector)

        # 2. Keyword intersection (raw + morphological stem matching)
        sol_keywords = set(extract_keywords(sol_doc, top_n=25))
        common_keywords = set(query_keywords.intersection(sol_keywords))

        # Check morphological root matches (e.g., 'impacts' <-> 'impact', 'drops' <-> 'drop')
        q_stems = {stem(k): k for k in query_keywords}
        s_stems = {stem(k): k for k in sol_keywords}
        for st_key, orig_q in q_stems.items():
            if st_key in s_stems and len(st_key) >= 3:
                common_keywords.add(orig_q)
        
        # Overlap coefficient: ratio relative to smaller set + bonus for multiple shared keywords
        min_kw_len = max(min(len(query_keywords), len(sol_keywords)), 1)
        overlap_score = len(common_keywords) / min_kw_len
        kw_count_bonus = min(0.30, len(common_keywords) * 0.08)

        # Category bonus: if category matches query text explicitly
        sol_cat = sol.get('category', '').lower()
        cat_bonus = 0.15 if sol_cat and sol_cat in query_text.lower() else 0.0

        # Calibrated cosine similarity (TF-IDF cosine sim on document pairs typically tops out around 0.5-0.6)
        scaled_cos = min(1.0, cos_sim * 1.6)

        # Hybrid final score calculation:
        # 45% Scaled Cosine Sim + 35% Keyword Overlap + Keyword Count Bonus + 15% Category match
        hybrid_score = (0.45 * scaled_cos) + (0.35 * overlap_score) + kw_count_bonus + cat_bonus
        relevance_percentage = round(min(hybrid_score * 100, 99.0), 1)

        # Filter out negligible matches
        if hybrid_score < min_score_threshold and not common_keywords:
            continue

        # Generate explainable justification
        common_kw_list = sorted(list(common_keywords))
        kw_display = ", ".join(common_kw_list[:5]) if common_kw_list else "thematic context"
        
        if relevance_percentage >= 70:
            match_quality = "High Match"
            explanation = (
                f"Strong semantic correspondence with key terms ({kw_display}). "
                f"Addresses core constraints and functional category."
            )
        elif relevance_percentage >= 40:
            match_quality = "Moderate Match"
            explanation = (
                f"Good contextual overlap in ({kw_display}). "
                f"This solution offers an adaptable approach for similar problem requirements."
            )
        else:
            match_quality = "Potential Adjacent Solution"
            explanation = (
                f"Partial keyword alignment ({kw_display}). "
                f"May provide structural ideas or components adaptable to this challenge."
            )

        match_item = dict(sol)
        match_item.update({
            "relevance_score": relevance_percentage,
            "match_quality": match_quality,
            "matched_keywords": common_kw_list,
            "explanation": explanation,
            "is_verified": False  # Explicitly labeled as algorithmic suggestion
        })
        ranked_results.append(match_item)

    # Sort descending by relevance score
    ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return ranked_results
