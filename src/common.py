"""
This module provides utility functions for loading datasets, preprocessing text,
and saving evaluation data for machine learning models.
"""

# pylint: disable=E0401, E0611
import os
import re
import json
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd


# Load the dataset
def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load dataset from a CSV file and fill missing values in the 'Synopsis' column.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The loaded dataset with filled 'Synopsis' column.
    """
    df = pd.read_csv(file_path)
    df["synopsis"] = df["synopsis"].fillna("")
    return df


# Basic text preprocessing
def preprocess_text(text: Optional[str]) -> str:
    """
    Preprocess the input text by converting it to lowercase and removing extra spaces.

    Args:
        text (str): The input text to preprocess.

    Returns:
        str: The preprocessed text.
    """
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)  # Remove extra spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove punctuation
    return text


# Save evaluation data
def save_evaluation_data(
    model_name: str,
    batch_size: int,
    num_embeddings: int,
    additional_info: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save evaluation data including timestamp and model parameters to a JSON file.

    Args:
        model_name (str): The name of the model.
        batch_size (int): The batch size used for generating embeddings.
        num_embeddings (int): Number of embeddings generated.
        additional_info (dict, optional): Additional information to save.
    """
    evaluation_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_parameters": {
            "model_name": model_name,
            "batch_size": batch_size,
            "num_embeddings": num_embeddings,
        },
    }

    if additional_info:
        evaluation_data.update(additional_info)

    # Path to the JSON file
    file_path = "model/evaluation_results.json"

    # Check if the file exists and is not empty
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        # Read the existing data
        with open(file_path, "r+", encoding="utf-8") as f:
            f.seek(0, os.SEEK_END)
            f.seek(f.tell() - 1, os.SEEK_SET)
            f.truncate()
            f.write(",\n")
            json.dump(evaluation_data, f, indent=4)
            f.write("\n]")
    else:
        # Create a new file with an array
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([evaluation_data], f, indent=4)
