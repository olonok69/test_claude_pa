# Neo4j Data Pipeline for BVA/LVA Event Analysis

This folder contains a series of Jupyter notebooks that build a Neo4j graph database for analyzing visitor attendance and session data from veterinary conferences (BVA - British Veterinary Association and LVA - London Vet Show).

## Overview

The pipeline creates a knowledge graph connecting:
- Visitors across multiple years and events
- Sessions/seminars attended by visitors
- Streams (topic categories) for sessions
- Job roles and specializations mapped to relevant streams

## Notebooks

### 1. `Neo4J_dva_registration.ipynb`
**Purpose**: Loads visitor registration data into Neo4j

**Key Operations**:
- Creates `Visitor_this_year` nodes from current BVA registration data
- Creates `Visitor_last_year_bva` nodes from previous year's BVA data
- Creates `Visitor_last_year_lva` nodes from previous year's LVA data

**Node Types Created**:
- `Visitor_this_year`
- `Visitor_last_year_bva` 
- `Visitor_last_year_lva`

### 2. `Neo4J_dva_sessions.ipynb`
**Purpose**: Loads session/seminar data and creates stream relationships

**Key Operations**:
- Creates `Sessions_this_year` nodes for current year sessions
- Creates `Sessions_past_year` nodes for previous year sessions (both BVA and LVA)
- Creates `Stream` nodes representing topic categories
- Establishes `HAS_STREAM` relationships between sessions and their streams

**Node Types Created**:
- `Sessions_this_year`
- `Sessions_past_year`
- `Stream`

**Relationships Created**:
- `(Session)-[:HAS_STREAM]->(Stream)`

### 3. `Neo4J_dva_scan_data.ipynb`
**Purpose**: Links visitors across years and tracks session attendance

**Key Operations**:
- Creates `Same_Visitor` relationships to connect the same person across different years/events
- Loads scan data showing which sessions visitors attended
- Creates `attended_session` relationships between visitors and sessions

**Relationships Created**:
- `(Visitor_this_year)-[:Same_Visitor]->(Visitor_last_year_bva/lva)`
- `(Visitor)-[:attended_session]->(Session)`

### 4. `Neo4J_stream_to_job.ipynb`
**Purpose**: Maps job roles to relevant content streams

**Key Operations**:
- Reads job role to stream mapping from CSV
- Creates `job_to_stream` relationships based on visitor job roles
- Helps identify which content streams are relevant for different professional roles

**Relationships Created**:
- `(Visitor_this_year)-[:job_to_stream]->(Stream)`

### 5. `Neo4J_stream_to_spezialization.ipynb`
**Purpose**: Maps practice specializations to relevant content streams

**Key Operations**:
- Processes visitor specialization data (e.g., "Small Animal", "Dairy", "Wildlife")
- Maps specializations to standardized categories
- Creates relationships between visitors and streams based on their specializations

**Relationships Created**:
- `(Visitor)-[:spezialization_to_stream]->(Stream)`

## Data Flow

1. **Registration Data** → Create visitor nodes
2. **Session Data** → Create session and stream nodes
3. **Identity Matching** → Link visitors across years
4. **Scan Data** → Track session attendance
5. **Professional Mapping** → Connect visitors to relevant streams based on job/specialization

## Prerequisites

- Neo4j database running locally (default: `bolt://127.0.0.1:7687`)
- Python packages: `neo4j`, `pandas`, `csv`, `json`
- CSV data files in `data/bva/` directory

## Usage

Run the notebooks in the numbered order above to build the complete graph database. Each notebook is self-contained but depends on the data structures created by previous notebooks.

## Graph Schema Summary

**Nodes**:
- Visitor nodes (this year, last year BVA/LVA)
- Session nodes (this year, past year)
- Stream nodes (topic categories)

**Relationships**:
- Same_Visitor (identity linking)
- attended_session (attendance tracking)
- HAS_STREAM (session categorization)
- job_to_stream (professional relevance)
- spezialization_to_stream (practice area relevance)

This graph structure enables complex queries about visitor behavior, content preferences, and professional development paths across multiple events and years.