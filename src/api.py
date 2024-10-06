"""
This module implements a Flask application that provides API endpoints
for finding the most similar anime or manga descriptions based on a given model
and description.

The application uses Sentence Transformers to encode descriptions and
calculate cosine similarities between them. It supports multiple synopsis
columns from a dataset and returns the top N most similar descriptions.
"""

# pylint: disable=import-error, global-variable-not-assigned, global-statement

import os
import warnings
import logging
import gc
import threading
import time
from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import torch
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Disable oneDNN for TensorFlow
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from sentence_transformers import (  # pylint: disable=wrong-import-position  # noqa: E402
    SentenceTransformer,
    util,
)

# Suppress the specific FutureWarning and DeprecationWarning from transformers
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=r"`clean_up_tokenization_spaces` was not set. It will be set to `True` by default.",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Variable to track the last request time
last_request_time = time.time()


def periodic_memory_clear():
    """
    Periodically clears memory if the application has been inactive for a specified duration.

    This function runs in a separate thread and checks the time since the last request.
    If the time exceeds 60 seconds, it clears the GPU cache and performs garbage collection
    to free up memory resources.

    The function logs the start of the thread and each memory clearing event.
    """
    global last_request_time
    logging.info("Starting the periodic memory clear thread.")
    while True:
        current_time = time.time()
        if current_time - last_request_time > 60:
            logging.info("Clearing memory due to inactivity.")
            torch.cuda.empty_cache()
            gc.collect()
        time.sleep(60)


threading.Thread(target=periodic_memory_clear, daemon=True).start()

# Initialize the limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["1 per second"])

# Load the merged datasets
anime_df = pd.read_csv("model/merged_anime_dataset.csv")
manga_df = pd.read_csv("model/merged_manga_dataset.csv")

# List of synopsis columns to consider for anime and manga
anime_synopsis_columns = [
    "synopsis",
    "Synopsis anime_dataset_2023",
    "Synopsis animes dataset",
    "Synopsis anime_270 Dataset",
    "Synopsis Anime-2022 Dataset",
    "Synopsis anime4500 Dataset",
    "Synopsis wykonos Dataset",
    "Synopsis Anime_data Dataset",
    "Synopsis anime2 Dataset",
    "Synopsis mal_anime Dataset",
]

manga_synopsis_columns = [
    "synopsis",
    "Synopsis jikan Dataset",
    "Synopsis data Dataset",
]


def load_embeddings(model_name, col, dataset_type):
    """
    Load embeddings for a given model and column.

    Args:
        model_name (str): The name of the model used to generate embeddings.
        col (str): The column name for which embeddings are to be loaded.
        dataset_type (str): The type of dataset ('anime' or 'manga').

    Returns:
        np.ndarray: A numpy array containing the embeddings for the specified column.

    Raises:
        FileNotFoundError: If the embeddings file does not exist.
    """
    embeddings_file = (
        f"model/{dataset_type}/{model_name}/embeddings_{col.replace(' ', '_')}.npy"
    )
    return np.load(embeddings_file)


def calculate_cosine_similarities(model, model_name, new_embedding, col, dataset_type):
    """
    Calculate cosine similarities between new embedding and existing embeddings for a given column.

    Args:
        model (SentenceTransformer): The sentence transformer model used for encoding.
        new_embedding (np.ndarray): The embedding of the new description.
        col (str): The column name for which to calculate similarities.
        dataset_type (str): The type of dataset ('anime' or 'manga').

    Returns:
        np.ndarray: A numpy array of cosine similarity scores.

    Raises:
        ValueError: If the dimensions of the existing embeddings do not match
                    the model's embedding dimension.
    """
    existing_embeddings = load_embeddings(model_name, col, dataset_type)
    if existing_embeddings.shape[1] != model.get_sentence_embedding_dimension():
        raise ValueError(f"Incompatible dimension for embeddings in {col}")
    return (
        util.pytorch_cos_sim(
            torch.tensor(new_embedding), torch.tensor(existing_embeddings)
        )
        .flatten()
        .cpu()
        .numpy()
    )


def find_top_similarities(cosine_similarities_dict, num_similarities=10):
    """
    Find the top N most similar descriptions across all columns based on cosine similarity scores.

    Args:
        cosine_similarities_dict (dict): A dictionary where keys are column names
            and values are arrays of cosine similarity scores.
        num_similarities (int, optional): The number of top similarities to find.
            Defaults to 10.

    Returns:
        list: A list of tuples, containing the index and column name of the similar descriptions.
    """
    all_top_indices = []
    for col, cosine_similarities in cosine_similarities_dict.items():
        top_indices_unsorted = np.argsort(cosine_similarities)[-num_similarities:]
        top_indices = top_indices_unsorted[
            np.argsort(cosine_similarities[top_indices_unsorted])[::-1]
        ]
        all_top_indices.extend([(idx, col) for idx in top_indices])
    all_top_indices.sort(
        key=lambda x: cosine_similarities_dict[x[1]][x[0]], reverse=True
    )
    return all_top_indices


def get_similarities(model_name, description, dataset_type):
    """
    Find and return the top N most similar descriptions for a given dataset type.

    Args:
        model_name (str): The name of the model to use.
        description (str): The description to compare against the dataset.
        dataset_type (str): The type of dataset ('anime' or 'manga').

    Returns:
        list: List of dictionaries containing top similar descriptions and their similarity scores.
    """
    global last_request_time
    last_request_time = time.time()  # Update last request time

    # Select the appropriate dataset and synopsis columns
    if dataset_type == "anime":
        df = anime_df
        synopsis_columns = anime_synopsis_columns
    else:
        df = manga_df
        synopsis_columns = manga_synopsis_columns

    model = SentenceTransformer(model_name)
    processed_description = description.lower().strip()
    new_pooled_embedding = model.encode([processed_description])

    cosine_similarities_dict = {
        col: calculate_cosine_similarities(
            model, model_name, new_pooled_embedding, col, dataset_type
        )
        for col in synopsis_columns
    }

    all_top_indices = find_top_similarities(cosine_similarities_dict)

    seen_names = set()
    results = []

    for idx, col in all_top_indices:
        name = df.iloc[idx]["title"]
        if name not in seen_names:
            synopsis = df.iloc[idx][col]
            similarity = float(cosine_similarities_dict[col][idx])
            results.append(
                {
                    "rank": len(results) + 1,
                    "name": name,
                    "synopsis": synopsis,
                    "similarity": similarity,
                }
            )
            seen_names.add(name)
            if len(results) >= 10:
                break

    # Clear memory
    del model, new_pooled_embedding, cosine_similarities_dict
    torch.cuda.empty_cache()
    gc.collect()

    return results


@app.route("/anisearchmodel/anime", methods=["POST"])
@limiter.limit("1 per second")
def get_anime_similarities():
    """
    Handle POST requests to find and return the top N most similar anime descriptions.

    Expects a JSON payload with 'model' and 'description' fields.

    Returns:
        Response: A JSON response with the top similar anime descriptions and the similarity scores.

    Raises:
        400 Bad Request: If the 'model' or 'description' fields are missing from the request.
    """
    try:
        data = request.json
        model_name = data.get("model")
        description = data.get("description")

        logging.info(
            "Received anime request with model: %s and description: %s",
            model_name,
            description,
        )

        if not model_name or not description:
            logging.error("Model name or description missing in the request.")
            return jsonify({"error": "Model name and description are required"}), 400

        results = get_similarities(model_name, description, "anime")
        logging.info("Returning %d anime results", len(results))
        return jsonify(results)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/anisearchmodel/manga", methods=["POST"])
@limiter.limit("1 per second")
def get_manga_similarities():
    """
    Handle POST requests to find and return the top N most similar manga descriptions.

    Expects a JSON payload with 'model' and 'description' fields.

    Returns:
        Response: A JSON response with the top similar manga descriptions and the similarity scores.

    Raises:
        400 Bad Request: If the 'model' or 'description' fields are missing from the request.
    """
    try:
        data = request.json
        model_name = data.get("model")
        description = data.get("description")

        logging.info(
            "Received manga request with model: %s and description: %s",
            model_name,
            description,
        )

        if not model_name or not description:
            logging.error("Model name or description missing in the request.")
            return jsonify({"error": "Model name and description are required"}), 400

        results = get_similarities(model_name, description, "manga")
        logging.info("Returning %d manga results", len(results))
        return jsonify(results)

    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1"]
    app.run(debug=debug_mode, threaded=True)