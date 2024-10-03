# AniSearchModel

This project involves generating and analyzing Sentence-BERT (SBERT) embeddings for an anime dataset. The goal is to preprocess, merge, and analyze anime data to find the most similar synopses using SBERT models.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Usage](#usage)
  - [Merging Datasets](#merging-datasets)
  - [Generating Embeddings](#generating-embeddings)
  - [Testing Embeddings](#testing-embeddings)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project performs the following operations:

- Loads and preprocesses multiple anime datasets.
- Merges datasets based on common identifiers.
- Generates SBERT embeddings for anime synopses.
- Calculates cosine similarities to find the most similar synopses.

## Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/RLAlpha49/AniSearchModel.git
   cd AniSearchModel
   ```

2. **Install dependencies:**

   Ensure you have Python installed, then run:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Merging Datasets

The repository already contains a merged dataset (`model/merged_anime_dataset`), but if you want to merge additional datasets, edit the `merge_datasets.py` file and run:

```bash
python merge_datasets.py
```

This script will load various datasets, preprocess names for matching, merge them based on identifiers, and save the merged dataset to `model/merged_anime_dataset.csv`.

### Generating Embeddings

To generate SBERT embeddings for the anime dataset, run:

```bash
python sbert.py --model <model_name>
```

Replace `<model-name>` with the desired SBERT model, e.g., `all-mpnet-base-v1`. This script will preprocess the text data, generate embeddings, and save them to disk.

### Testing Embeddings

To test the embeddings and find similar synopses, execute:

```bash
python test.py --model <model_name>
```

Replace `<model-name>` with the desired SBERT model, e.g., `all-mpnet-base-v1`. This script compares a new description against the dataset to find the most similar synopses using cosine similarity.

## Project Structure

- **merge_datasets.py**: Merges multiple anime datasets.
- **sbert.py**: Generates SBERT embeddings for the dataset.
- **test.py**: Tests the SBERT model by finding similar synopses.
- **common.py**: Contains utility functions for loading datasets and preprocessing text.
- **data/**: Directory for storing datasets.
- **model/**: Directory for storing models and embeddings.
- **model/merged_anime_dataset.csv**: Stores the merged anime dataset.
- **model/evaluation_results.json**: Stores evaluation data and results.

## Dependencies

- Python 3.6+
- pandas
- numpy
- torch
- transformers
- sentence-transformers
- tqdm
- datasets

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
