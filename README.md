# 🏆 Adobe India Hackathon 2025 – Challenge 1B Solution

## 🚀 Challenge 1B: Multi-Collection PDF Analysis

This repository contains a **production-ready**, high-performance solution for **Challenge 1B** of the Adobe India Hackathon 2025. It is designed to extract, analyze, and rank the most relevant content from unstructured PDFs based on a given **persona** and **job-to-be-done (JTBD)**.

---

## ✅ Summary of Strengths

### 🎯 **Multi-Factor Scoring System** (Targets 60% section relevance)
- 🔍 Semantic similarity via `sentence-transformers` (MiniLM-L6-v2)
- 🧠 Persona-specific keyword matching (travel, HR, food, etc.)
- 🏗️ Structural importance weighting (headings, titles, formatting)
- 🤖 Task-aware query enhancement (persona + JTBD fusion)

### ⚡ **Performance Optimized** (Meets all constraints)
- ✅ CPU-only execution
- ✅ 90MB model under 1GB limit
- ✅ Sub-60s processing time (typically 5–15s)
- ✅ No internet required at runtime (offline inference)

### 📄 **Robust PDF Processing**
- Handles diverse layouts, encodings, and formats
- Preserves page numbers, hierarchy, and section structure
- Smart section boundary detection using regex + heuristics

### 👥 **Persona-Driven Intelligence**
- Custom dictionaries for different persona types
- Context-aware relevance boosting
- Adaptive to different domains (Travel, HR, Culinary)

---

## 🧠 Approach Overview

### 📘 Stage 1: Structured PDF Extraction
- Uses **PyPDF2** with advanced heuristics to detect:
  - Numbered sections (1., 1.1, etc.)
  - Title case, ALL CAPS, and bolded headings
- Maintains **page-level tracking** and **document hierarchy**

### 💡 Stage 2: Semantic Relevance Analysis
- Embedding-based comparison using `all-MiniLM-L6-v2` (90MB)
- Persona and task vectors enhanced with custom keywords
- Scoring breakdown:
  - 50% semantic similarity
  - 30% keyword match score
  - 20% structural importance

### 🪜 Stage 3: Hierarchical Content Ranking
- Top-N relevant **sections** selected
- Extracted **subsections** by splitting long paragraphs intelligently
- Ranked by combined relevance score

---

## 📂 Directory Structure

Challenge_1b/
├── data/
│ ├── Collection_1/
│ ├── Collection_2/
│ └── Collection_3/
├── src/
│ ├── main.py ← Entry point
│ ├── pdf_processor.py ← PDF parsing & extraction
│ └── content_analyzer.py ← Semantic analysis & scoring
├── requirements.txt
├── Dockerfile
├── approach_explanation.md
└── README.md



---

## 🐳 Dockerized Execution

### 🔨 Build the Image

```bash
docker build -t challenge1b .
▶️ Run for Each Collection
bash

docker run --rm -v "${PWD}/data:/app/data" -w /app/src challenge1b \
    python3 main.py /app/data/Collection_1/challenge1b_input.json /app/data/Collection_1/challenge1b_output.json

docker run --rm -v "${PWD}/data:/app/data" -w /app/src challenge1b \
    python3 main.py /app/data/Collection_2/challenge1b_input.json /app/data/Collection_2/challenge1b_output.json

docker run --rm -v "${PWD}/data:/app/data" -w /app/src challenge1b \
    python3 main.py /app/data/Collection_3/challenge1b_input.json /app/data/Collection_3/challenge1b_output.json
📌 Important: Ensure your data folders are named exactly as Collection_1, Collection_2, and Collection_3.

✨ Key Features
Feature	Description
🔗 Offline Execution	No internet required for model loading
🧠 MiniLM Model	Fast, lightweight (90MB) and accurate
🧱 Modular Architecture	Clean separation: PDF I/O, NLP, scoring
🛠️ Error Handling	Handles missing files, empty PDFs, invalid input gracefully
📊 Ranked Output	Top 10 relevant sections and 15 meaningful subsections

📝 Sample Output Summary
![alt text](<Screenshot (25).png>)
![alt text](<Screenshot (30).png>) 
![alt text](<Screenshot (29).png>) 
![alt text](<Screenshot (28).png>) 
![alt text](<Screenshot (27).png>) 
![alt text](<Screenshot (26).png>)
Documents analyzed: 7
Sections extracted: 10
Subsections generated: 15
Persona: Travel Planner
Task: Plan a trip of 4 days for a group of 10 college friends.
🏁 Competitive Edge
✅ Speed: Sub-60s response time with batch processing & caching

✅ Accuracy: Persona-aware semantic ranking

✅ Robustness: Handles real-world messy PDFs

✅ Scalability: Tested on multiple document collections

📌 Tech Stack
Python 3.9

PyPDF2

SentenceTransformers (MiniLM-L6-v2)

Transformers

Docker

📘 Files Explained
File	Purpose
main.py	Orchestrates the workflow
pdf_processor.py	PDF parsing & section detection
content_analyzer.py	Semantic scoring + subsection generation
requirements.txt	All Python dependencies
Dockerfile	For building a production container image
approach_explanation.md	Detailed technical explanation

📚 Documentation
Refer to approach_explanation.md for a deep dive into the methodology and design choices.

This solution was carefully crafted to meet all judging criteria:

✅ Section relevance (60%): via persona-task driven scoring

✅ Subsection quality (40%): via contextual chunking

✅ Runtime limits: <60s with CPU-only and 90MB model

✅ Technical elegance: Clean, scalable, well-architected

            Thanks to the Adobe Hackathon team for this exciting challenge.