import json
from collections import Counter
from itertools import islice

def load_config(config_path):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    return config

def preprocess_text(text, config):
    # Extract config parameters
    allowed_characters = config["allowed_characters"]
    characters_to_replace = config["characters_to_replace"]
    replacement_character = config["replacement_character"]
    characters_to_skip = config["characters_to_skip"]
    characters_to_split = config["characters_to_split"]
    case_sensitive = config["case_sensitive"]
    
    # Convert text to lowercase if case sensitivity is turned off
    if not case_sensitive:
        text = text.lower()
        allowed_characters = allowed_characters.lower()
        characters_to_replace = characters_to_replace.lower()
        characters_to_skip = characters_to_skip.lower()
        characters_to_split = characters_to_split.lower()
    
    # Step 1: Replace specified characters
    text = ''.join([
        ch if ch in allowed_characters else
        replacement_character if ch in characters_to_replace else ch
        for ch in text
    ])
    
    # Step 2: Remove characters to skip
    text = ''.join([ch for ch in text if ch not in characters_to_skip])
    
    # Step 3: Split the text based on characters in characters_to_split
    split_chars = '|'.join([f'\\{ch}' for ch in characters_to_split])
    chunks = text.split(split_chars)
    
    # Join chunks together to form the final cleaned text for n-gram analysis
    return ''.join(chunks)

def generate_character_ngrams(text, n):
    """Generate n-grams from a string of characters."""
    return [text[i:i+n] for i in range(len(text) - n + 1)]

def most_common_ngrams(file_path, config):
    # Read the file content
    with open(file_path, 'r') as file:
        text = file.read()
    
    # Preprocess text based on allowed characters, replacement rules, and skip/split settings
    filtered_text = preprocess_text(text, config)
    
    # Generate n-grams and m-grams
    n = config["n"]
    m = config["m"]
    n_grams = generate_character_ngrams(filtered_text, n)
    m_grams = generate_character_ngrams(filtered_text, m)
    
    # Count the frequency of each n-gram and m-gram
    n_grams_count = Counter(n_grams)
    m_grams_count = Counter(m_grams)
    
    # Find the most common n-grams and m-grams
    top_n = config["top_n"]
    most_common_n_grams = [ngram for ngram, _ in n_grams_count.most_common(top_n)]
    most_common_m_grams = [mgram for mgram, _ in m_grams_count.most_common(top_n)]
    
    return most_common_n_grams, most_common_m_grams, filtered_text

def count_ngram_combinations(text, n_grams, m_grams, n, m):
    """Count occurrences of each (n-gram, m-gram) combination."""
    counts = {}
    # Generate n-grams and m-grams with their positions in the text
    n_gram_positions = {n_gram: [] for n_gram in n_grams}
    m_gram_positions = {m_gram: [] for m_gram in m_grams}
    
    # Collect positions for each n-gram
    for i in range(len(text) - n + 1):
        n_gram = text[i:i+n]
        if n_gram in n_gram_positions:
            n_gram_positions[n_gram].append(i)
    
    # Collect positions for each m-gram
    for i in range(len(text) - m + 1):
        m_gram = text[i:i+m]
        if m_gram in m_gram_positions:
            m_gram_positions[m_gram].append(i)
    
    # Count occurrences of each (n-gram, m-gram) pair by checking adjacency
    for n_gram in n_grams:
        for m_gram in m_grams:
            count = 0
            for n_pos in n_gram_positions[n_gram]:
                if n_pos + n == len(text):
                    break
                # Check if m-gram occurs right after the n-gram
                if text[n_pos + n:n_pos + n + m] == m_gram:
                    count += 1
            counts[(n_gram, m_gram)] = count
    return counts

def generate_ngram_matrix(n_grams, m_grams, counts):
    # Display the matrix
    print("N-gram / M-gram Combination Matrix with Counts:")
    print("       " + "  ".join([f"{m}" for m in m_grams]))  # Header row for m-grams
    for i, n_gram in enumerate(n_grams):
        row_str = "  ".join([f"{counts[(n_gram, m_gram)]}" for m_gram in m_grams])
        print(f"{n_gram}  {row_str}")

# Example usage
config_path = 'config.json'
file_path = 'your_text_file.txt'  # Replace with the path to your text file

# Load the config
config = load_config(config_path)

# Get the most common n-grams, m-grams, and preprocessed text
most_common_n_grams, most_common_m_grams, filtered_text = most_common_ngrams(file_path, config)

# Count occurrences of each (n-gram, m-gram) combination
ngram_combinations_counts = count_ngram_combinations(filtered_text, most_common_n_grams, most_common_m_grams, config["n"], config["m"])

# Generate and display the n-gram / m-gram combination matrix with counts
generate_ngram_matrix(most_common_n_grams, most_common_m_grams, ngram_combinations_counts)
