# Conference Attendee Clustering and Classification Project

## Overview

This project implements a machine learning system for clustering and classifying conference attendees based on their behavior patterns and session attendance. The system uses various embedding models (Mistral, LLaMA, Nomic) and classification techniques to categorize attendees into six distinct behavioral clusters.

## Behavioral Clusters

The project identifies six main attendee categories:

1. **Networking** - Attendees focused on making connections
2. **Learning** - Attendees primarily seeking educational content
3. **Searching** - Attendees exploring various options
4. **Sourcing: Early** - Early-stage procurement/sourcing activities
5. **Sourcing: In Process** - Mid-stage sourcing activities
6. **Sourcing: Deciding** - Late-stage decision-making phase

## Project Structure

### Phase 1 Files

#### 1. `CSM_generate_Embeddings_nomic.ipynb`
- Generates embeddings using various models (Mistral-7B, LLaMA, Nomic)
- Implements a neural network classifier (BadgeNet) for attendee classification
- Uses focal loss for handling class imbalance
- Achieves classification accuracy and generates predictions

**Key Features:**
- Custom `BadgeDataset` class for loading badge and embedding data
- 4-layer neural network architecture
- Training with cross-entropy loss
- Prediction pipeline for new attendees

#### 2. `Cluster_embeddings_nomic_vs_mistral_llama.ipynb`
- Compares clustering performance across different embedding models
- Generates cluster nomenclature embeddings
- Uses cosine similarity for cluster assignment
- Provides comparative analysis of Mistral, LLaMA, and Nomic embeddings

**Key Models Used:**
- Mistral-7B-v0.1
- LLaMA-3.2-3B-Instruct
- Nomic-embed-text-v1

#### 3. `Prompt_OLLama_DeepSeek_Phi3_5_LLama3_2.ipynb`
- Implements prompt-based classification using various LLMs
- Uses few-shot learning with examples from each category
- Tests multiple models including DeepSeek R1, LLaMA 3.2, and Phi 3.5

**Prompt Structure:**
- Category descriptions
- One example per category
- Text to classify
- Constrained output to class labels only

#### 4. `load.py`
- Utility script for loading embeddings from JSON files
- Handles NaN values in embeddings
- Converts JSON data to numpy arrays for processing

#### 5. `pysftp.ipynb`
- File transfer utilities for moving embeddings between systems
- Uses SFTP for secure file transfer

#### 6. `Cluster_embeddings_nomic_vs_mistral_llama.ipynb`


### Purpose
This notebook generates vector embeddings for session data in a Customer Success Management system. The embeddings are created from aggregated session information and can be used for similarity matching, recommendation engines, or clustering similar sessions.

### Key Components

1. **Data Processing Pipeline**
   - Loads session data from JSON files containing aggregated information about badges/sessions
   - Processes structured data with fields like `BadgeId`, `SessionInfo`, and `AggregatedInfo`
   - Handles multiple sessions per badge ID

2. **Embedding Models Tested**
   - **Mistral 7B v0.1**: 4096-dimensional embeddings, 32k context window
   - **Llama 3.2 3B**: 3072-dimensional embeddings, 128k context window  
   - **NOMIC-embed-text-v1**: 768-dimensional embeddings, 8192 context length

3. **Performance Metrics**
   - Mistral 7B: ~49 seconds processing time
   - Llama 3.2 3B: ~17 seconds processing time
   - NOMIC (GPU): ~4 seconds processing time
   - NOMIC (CPU): ~52 seconds processing time

4. **Key Functions**
   - `generate_session_embeddings_all_json()`: Main function that processes all sessions and generates embeddings
   - Uses the second-to-last layer of transformer models for richer representations
   - Saves embeddings as JSON files for downstream use

5. **Similarity Testing**
   - Includes cosine similarity calculations between sample sessions
   - Implements custom cosine distance function for verification
   - Tests similarity between sessions 37780 and 37781 as examples



### Technical Details
- Uses 8-bit quantization for memory efficiency with larger models
- Handles GPU memory management with cache clearing
- Supports batch processing of large session datasets
- Outputs embeddings in JSON format for easy integration

#### 7. `CSM_generate_Embeddings_badges.ipynb`


## Purpose
The notebook creates vector embeddings for badge holder information, converting aggregated text data about conference attendees into numerical representations that can be used for similarity matching, clustering, or recommendation systems.

## Key Components

### 1. **Data Loading**
- Loads badge data from `badge_id_aggregated_results.json`
- Each badge has an ID and associated "AggregatedInfo" text
- The notebook shows there are multiple badge entries (examples shown include BadgeId_22A5D99 and BadgeId_22DIQKA)

### 2. **Embedding Models Used**
The notebook tests three different language models for generating embeddings:

- **Mistral 7B**: 
  - Produces 4096-dimensional embeddings
  - Takes ~2 hours 57 minutes on GPU for badge embeddings
  - 8-bit quantization used for memory efficiency

- **LLaMA 3.2B**:
  - Produces 3072-dimensional embeddings  
  - Takes ~1 hour on GPU
  - Also uses 8-bit quantization

- **NOMIC-embed-text-v1**:
  - Produces 768-dimensional embeddings
  - GPU time: ~33 minutes
  - CPU time: ~8 hours 22 minutes
  - Uses sentence-transformers library

### 3. **Main Function**
The `generate_session_embeddings_all_json()` function:
- Iterates through badge data
- Tokenizes the AggregatedInfo text (max 512 tokens)
- Generates embeddings using the model's hidden states (second-to-last layer)
- Saves embeddings as JSON files

### 4. **Similarity Testing**
- Implements cosine distance calculation to measure similarity between badge embeddings
- Tests similarity between sample badges to verify embedding quality

### 5. **Memory Management**
- Includes explicit garbage collection and CUDA cache clearing between models
- Essential for running multiple large models sequentially

## Use Case
This appears to be part of a recommendation or matching system for conference attendees, where badge holder information (likely including interests, sessions attended, or profile data) is converted to embeddings for finding similar attendees or making personalized recommendations.

The comparison of multiple embedding models suggests the team is evaluating which model provides the best balance of performance, embedding quality, and computational efficiency for their specific use case.


## Dependencies

```python
# Core ML Libraries
- torch
- transformers
- sentence-transformers
- sklearn
- numpy
- pandas

# Specialized Libraries
- bitsandbytes (for model quantization)
- langchain-ollama (for LLM integration)
- pysftp (for file transfer)
- faker (for data generation)

# Visualization and Utils
- tqdm
- matplotlib (implied)
```

## Model Configuration

### Embedding Models
```yaml
clustering_config:
  # Huggingface access token
  access_token: "hb-token"
  
  # Model options
  model_name: 
    - "mistralai/Mistral-7B-v0.1"
    - "meta-llama/Meta-Llama-3-8B"
    - "meta-llama/Llama-3.2-3B-Instruct"
    - "nomic-ai/nomic-embed-text-v1"
  
  backend_type: "transformers"
  clustering_algorithm: "kmeans"
```

## Neural Network Architecture

```python
BadgeNet:
  - Input Layer: [embedding_size] → 128
  - Hidden Layer 1: 128 → 64
  - Hidden Layer 2: 64 → 64
  - Output Layer: 64 → [num_classes]
  - Activation: ReLU
```

## Training Configuration

- **Batch Size**: 32
- **Epochs**: 400
- **Learning Rate**: 0.001
- **Optimizer**: Adam
- **Loss Function**: Cross-Entropy / Focal Loss
- **Validation Split**: Configurable

## Usage

### 1. Generate Embeddings
```python
# Load session data
session_data = json.load(open(session_data_path))

# Generate embeddings using chosen model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id, device_map="auto", load_in_8bit=True)

# Process and save embeddings
embeddings = generate_embeddings(session_data, model, tokenizer)
```

### 2. Train Classifier
```python
# Initialize dataset
train_db = BadgeDataset(csv_path, json_path, split="train")

# Create model and train
model = BadgeNet(input_size=1024, num_classes=5)
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop with evaluation metrics
```

### 3. Predict Classifications
```python
# Load trained model
model = load_model(model_path, input_size, num_classes)

# Predict on new data
predictions = predict_classes(model, embeddings_json, output_csv)
```

## Clustering Approach

The project uses two complementary approaches:

1. **Embedding-based Clustering**: Uses cosine similarity between attendee embeddings and cluster nomenclature embeddings
2. **Neural Network Classification**: Supervised learning using labeled data

## Performance Metrics

- Classification accuracy
- Precision, Recall, F1-Score per class
- Class distribution analysis
- Confusion matrix (implied)

## Data Format

### Input Data
- CSV files with BadgeId and ClusterId columns
- JSON files with aggregated session information
- Embeddings stored as JSON with structure: `{"BadgeId_XXX": [[embedding_vector]]}`

### Output Data
- CSV predictions with BadgeId and predicted ClusterId
- Model checkpoints (.pth files)
- Embedding files in JSON format

## Notes

- The project handles class imbalance (note: "Sourcing: Deciding" class may be missing in newer datasets)
- Supports both 5-class and 6-class classification scenarios
- Uses 8-bit quantization for efficient model loading
- Implements robust error handling for NaN values in embeddings

## Future Improvements

- Implement cross-validation for more robust evaluation
- Add support for additional embedding models
- Implement ensemble methods combining multiple models
- Add real-time classification API
- Enhance visualization of clustering results