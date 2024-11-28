import csv
import json
import re
from collections import Counter

from colour import Color

# Load config as a global variable
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, "r") as config_file:
    config = json.load(config_file)


def preprocess_text(text):
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

    # Replace specified characters
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

    # Remove characters to skip
    text = "".join([ch for ch in text if ch not in characters_to_skip])

    return text


def generate_character_ngrams(text, n):
    """Generate n-grams from a string of characters."""
    characters_to_split = config["characters_to_split"]
    return [
        text[i : i + n]
        for i in range(len(text) - n + 1)
        if not any(ch in characters_to_split for ch in text[i : i + n])
    ]


def most_common_ngrams():
    # Read the file content
    with open(config["input_file"], "r") as file:
        text = file.read()

    # Preprocess text based on allowed characters, replacement rules, and skip/split settings
    filtered_text = preprocess_text(text)

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
    n_gram_positions = {n_gram: [] for n_gram in n_grams}
    m_gram_positions = {m_gram: [] for m_gram in m_grams}

    for i in range(len(text) - n + 1):
        n_gram = text[i : i + n]
        if n_gram in n_gram_positions:
            n_gram_positions[n_gram].append(i)

    for i in range(len(text) - m + 1):
        m_gram = text[i : i + m]
        if m_gram in m_gram_positions:
            m_gram_positions[m_gram].append(i)

    for n_gram in n_grams:
        for m_gram in m_grams:
            count = 0
            for n_pos in n_gram_positions[n_gram]:
                if n_pos + n == len(text):
                    break
                if text[n_pos + n : n_pos + n + m] == m_gram:
                    count += 1
            counts[(n_gram, m_gram)] = count
    return counts


def generate_ngram_matrix(n_grams, m_grams, counts):
    output_file = config["output_file"]
    with open(output_file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        header = [""] + m_grams
        csvwriter.writerow(header)
        for n_gram in n_grams:
            row = [n_gram] + [counts.get((n_gram, m_gram), 0) for m_gram in m_grams]
            csvwriter.writerow(row)
    print(f"N-gram / M-gram Combination Matrix written to {output_file}")


def generate_html_ngram_matrix(n_grams, m_grams, counts, colors):
    output_html_file = config["output_html_file"]
    darkmode = config["darkmode"]
    max_count = max(counts.values(), default=1)
    min_count = min(counts.values(), default=0)

    # Generate a three-color gradient
    gradient_list = list(colors[0].range_to(colors[1], max_count // 2))
    gradient_list += list(colors[1].range_to(colors[2], max_count // 2))
    gradient_list.insert(0, Color("#19191b") if darkmode else Color("white"))

    def color_gradient(count):
        return gradient_list[count]

    html_content = "<html><head><style>"
    html_content += "table { border-collapse: collapse; width: 100%; }"
    if darkmode:
        html_content += "body {background-color: #19191b; color: white}"
    html_content += (
        "th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }"
    )
    html_content += "</style></head><body><h2>N-gram / M-gram Combination Matrix</h2><table><tr><th></th>"

    for m_gram in m_grams:
        html_content += f"<th>{m_gram}</th>"
    html_content += "</tr>"

    for n_gram in n_grams:
        html_content += f"<tr><th>{n_gram}</th>"
        for m_gram in m_grams:
            count = counts.get((n_gram, m_gram), 0)
            color = color_gradient(count)
            html_content += f"<td style='background-color: {color}'>{count}</td>"
        html_content += "</tr>"

    html_content += "</table></body></html>"

    with open(output_html_file, "w") as html_file:
        html_file.write(html_content)

    print(f"N-gram / M-gram Combination Matrix HTML file saved to {output_html_file}")


def highlight_ngrams_by_frequency(
    most_common_n_grams, most_common_m_grams, input_file_path, output_html_path, colors
):
    # Read the input text
    with open(input_file_path, "r") as file:
        text = file.read()

    # Combine n-grams and m-grams into one list
    all_ngrams = most_common_n_grams + most_common_m_grams

    # Count the frequency of each n-gram in the text
    frequencies = Counter()
    for ngram in all_ngrams:
        frequencies[ngram] = len(
            re.findall(re.escape(ngram), text, flags=re.IGNORECASE)
        )

    # Determine the maximum frequency for scaling colors
    max_frequency = max(frequencies.values(), default=1)

    # Generate a three-color gradient
    low_color, mid_color, high_color = colors
    gradient = list(low_color.range_to(mid_color, max_frequency // 2))
    gradient += list(mid_color.range_to(high_color, max_frequency // 2 + 1))

    # Map each n-gram to its frequency-based color
    ngram_colors = {
        ngram: gradient[freq - 1].hex for ngram, freq in frequencies.items()
    }

    # Sort n-grams by length to prioritize longer matches
    all_ngrams.sort(key=len, reverse=True)

    # Escape special characters in n-grams for regex
    escaped_patterns = [(re.escape(ngram), ngram_colors[ngram]) for ngram in all_ngrams]

    # Function to wrap matches with span tags
    def replace_match(match):
        for pattern, color in escaped_patterns:
            if re.fullmatch(pattern, match.group(0)):
                return (
                    f"<span style='background-color: {color};'>{match.group(0)}</span>"
                )
        return match.group(0)

    # Use regex to safely wrap each n-gram/m-gram
    regex = re.compile("|".join(pattern for pattern, _ in escaped_patterns))
    highlighted_text = regex.sub(replace_match, text)

    # Generate the HTML content
    html_content = f"""
    <html>
    <head>
        <title>Frequency-Based Highlighted N-Grams</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                padding: 20px;
                background-color: #f9f9f9;
                color: #333;
            }}
            span {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Highlighted Text with Frequency-Based Colors</h1>
        <p>{highlighted_text}</p>
    </body>
    </html>
    """

    # Write the HTML content to the output file
    with open(output_html_path, "w") as html_file:
        html_file.write(html_content)

    print(
        f"Highlighted n-grams with frequency-based colors saved to {output_html_path}"
    )


def main():
    # Main Execution
    colors = [Color("blue"), Color("lime"), Color("red")]
    most_common_n_grams, most_common_m_grams, filtered_text = most_common_ngrams()
    ngram_combinations_counts = count_ngram_combinations(
        filtered_text,
        most_common_n_grams,
        most_common_m_grams,
        config["n"],
        config["m"],
    )

    generate_ngram_matrix(
        most_common_n_grams, most_common_m_grams, ngram_combinations_counts
    )
    generate_html_ngram_matrix(
        most_common_n_grams, most_common_m_grams, ngram_combinations_counts, colors
    )
    highlight_ngrams_by_frequency(
        most_common_n_grams,
        most_common_m_grams,
        config["input_file"],
        config["output_highlighted_text"],
        colors,
    )


main()
