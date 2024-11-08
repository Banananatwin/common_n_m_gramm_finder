import csv
import json
from collections import Counter
from itertools import islice


def load_config(config_path):
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
    return config


def preprocess_text(text, config):
    # Extract config parameters
    allowed_characters = config["allowed_characters"]
    characters_to_replace = config["characters_to_replace"]
    replacement_character = config["replacement_character"]
    characters_to_skip = config["characters_to_skip"]
    case_sensitive = config["case_sensitive"]

    # Convert text to lowercase if case sensitivity is turned off
    if not case_sensitive:
        text = text.lower()
        allowed_characters = allowed_characters.lower()
        characters_to_replace = characters_to_replace.lower()
        characters_to_skip = characters_to_skip.lower()

    # Step 1: Replace specified characters
    text = "".join(
        [
            ch
            if ch in allowed_characters
            else replacement_character
            if ch in characters_to_replace
            else ch
            for ch in text
        ]
    )

    # Step 2: Remove characters to skip
    text = "".join([ch for ch in text if ch not in characters_to_skip])

    # Join chunks together to form the final cleaned text for n-gram analysis
    return text


def generate_character_ngrams(text, n, config):
    """Generate n-grams from a string of characters."""
    characters_to_split = config["characters_to_split"]
    return [
        text[i : i + n]
        for i in range(len(text) - n + 1)
        if not any(ch in characters_to_split for ch in text[i : i + n])
    ]


def most_common_ngrams(file_path, config):
    # Read the file content
    with open(file_path, "r") as file:
        text = file.read()

    # Preprocess text based on allowed characters, replacement rules, and skip/split settings
    filtered_text = preprocess_text(text, config)

    # Generate n-grams and m-grams
    n = config["n"]
    m = config["m"]
    n_grams = generate_character_ngrams(filtered_text, n, config)
    m_grams = generate_character_ngrams(filtered_text, m, config)

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
        n_gram = text[i : i + n]
        if n_gram in n_gram_positions:
            n_gram_positions[n_gram].append(i)

    # Collect positions for each m-gram
    for i in range(len(text) - m + 1):
        m_gram = text[i : i + m]
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
                if text[n_pos + n : n_pos + n + m] == m_gram:
                    count += 1
            counts[(n_gram, m_gram)] = count
    return counts


def generate_ngram_matrix(n_grams, m_grams, counts, output_file):
    with open(output_file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)

        # Write header row with m-grams
        header = [""] + m_grams
        csvwriter.writerow(header)

        # Write each row for n-grams
        for n_gram in n_grams:
            row = [n_gram] + [counts.get((n_gram, m_gram), 0) for m_gram in m_grams]
            csvwriter.writerow(row)

    print(f"N-gram / M-gram Combination Matrix written to {output_file}")


def generate_html_ngram_matrix(n_grams, m_grams, counts, output_html_file):
    """Generate an HTML table with color-coded cells based on n-gram/m-gram combination counts."""

    # Determine the minimum and maximum counts for scaling colors
    max_count = max(counts.values(), default=1)
    min_count = min(counts.values(), default=0)

    def color_gradient(count):
        """Return a color from green (low) to red (high) based on count."""
        if max_count == min_count:
            return "#ff0000"  # Only red if there's a single value for all counts
        # Scale count to range 0-255, with higher counts closer to red
        scale = int(255 * (count - min_count) / (max_count - min_count))
        red = 255
        green = 255 - scale
        return f"rgb({red},{green},0)"

    # Start the HTML content
    html_content = "<html><head><style>"
    html_content += "table { border-collapse: collapse; width: 100%; }"
    html_content += (
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }"
    )
    html_content += "</style></head><body>"
    html_content += "<h2>N-gram / M-gram Combination Matrix</h2>"
    html_content += "<table><tr><th></th>"

    # Header row with m-grams
    for m_gram in m_grams:
        html_content += f"<th>{m_gram}</th>"
    html_content += "</tr>"

    # Rows with n-grams and color-coded counts
    for n_gram in n_grams:
        html_content += f"<tr><th>{n_gram}</th>"
        for m_gram in m_grams:
            count = counts.get((n_gram, m_gram), 0)
            color = color_gradient(count)
            html_content += f"<td style='background-color: {color}'>{count}</td>"
        html_content += "</tr>"

    # Close HTML tags
    html_content += "</table></body></html>"

    # Write the HTML content to the output file
    with open(output_html_file, "w") as html_file:
        html_file.write(html_content)

    print(f"N-gram / M-gram Combination Matrix HTML file saved to {output_html_file}")


# Example usage
config_path = "config.json"

# Load the config
config = load_config(config_path)

input_file_path = config["input_file"]
output_file_path = config["output_file"]

# Get the most common n-grams, m-grams, and preprocessed text
most_common_n_grams, most_common_m_grams, filtered_text = most_common_ngrams(
    input_file_path, config
)

# Count occurrences of each (n-gram, m-gram) combination
ngram_combinations_counts = count_ngram_combinations(
    filtered_text, most_common_n_grams, most_common_m_grams, config["n"], config["m"]
)

# Generate and display the n-gram / m-gram combination matrix with counts
generate_ngram_matrix(
    most_common_n_grams,
    most_common_m_grams,
    ngram_combinations_counts,
    output_file_path,
)

output_html_file = config["output_html_file"]  # Set this in your config file
generate_html_ngram_matrix(
    most_common_n_grams,
    most_common_m_grams,
    ngram_combinations_counts,
    output_html_file,
)
