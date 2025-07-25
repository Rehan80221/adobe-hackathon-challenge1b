#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import our custom modules
from pdf_processor import PDFProcessor
from content_analyzer import ContentAnalyzer

def load_input_config(input_path: str) -> Dict:
    """Load and validate input configuration"""
    try:
        with open(input_path, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['documents', 'persona', 'job_to_be_done']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        return config
    
    except Exception as e:
        print(f"Error loading input config: {e}")
        sys.exit(1)

def process_documents(documents_info: List[Dict], base_path: Path) -> List[Dict]:
    """Process all PDF documents and extract content"""
    
    pdf_processor = PDFProcessor()
    processed_docs = []
    
    pdfs_dir = base_path / 'PDFs'
    
    for doc_info in documents_info:
        filename = doc_info['filename']
        pdf_path = pdfs_dir / filename
        
        if not pdf_path.exists():
            print(f"Warning: PDF not found: {pdf_path}")
            continue
        
        print(f"Processing: {filename}")
        processed_doc = pdf_processor.extract_text_with_structure(str(pdf_path))
        
        if 'error' not in processed_doc:
            print(f"  - Extracted {len(processed_doc['sections'])} sections from {processed_doc['total_pages']} pages")
        else:
            print(f"  - Error processing {filename}: {processed_doc['error']}")
        
        processed_docs.append(processed_doc)
    
    return processed_docs

def analyze_content(documents: List[Dict], persona: str, job_task: str) -> tuple:
    """Analyze content and extract relevant sections"""
    
    print("\nAnalyzing content relevance...")
    content_analyzer = ContentAnalyzer()
    
    # Analyze all sections for relevance
    ranked_sections = content_analyzer.analyze_relevance(documents, persona, job_task)
    
    print(f"Found {len(ranked_sections)} sections total")
    
    # Extract top sections (limit to reasonable number for output)
    top_sections = ranked_sections[:20]  # Top 20 sections
    
    # Extract subsections from top sections
    print("Extracting detailed subsections...")
    subsections = content_analyzer.extract_subsections(top_sections[:5], persona, job_task)
    
    print(f"Generated {len(subsections)} subsections")
    
    return top_sections, subsections

def generate_output(input_config: Dict, top_sections: List[Dict], subsections: List[Dict]) -> Dict:
    """Generate the final output JSON structure"""
    
    # Extract metadata
    persona = input_config['persona']['role']
    job_task = input_config['job_to_be_done']['task']
    input_docs = [doc['filename'] for doc in input_config['documents']]
    
    # Format extracted sections (top 10 for final output)
    extracted_sections = []
    for i, section in enumerate(top_sections[:10]):
        extracted_sections.append({
            "document": section['document'],
            "section_title": section['clean_title'],
            "importance_rank": i + 1,
            "page_number": section['page_number']
        })
    
    # Format subsection analysis (top 15 for final output)
    subsection_analysis = []
    for subsection in subsections[:15]:
        # Truncate content to reasonable length
        content = subsection['content']
        if len(content) > 500:
            content = content[:497] + "..."
        
        subsection_analysis.append({
            "document": subsection['document'],
            "refined_text": content,
            "page_number": subsection['page_number']
        })
    
    # Build final output
    output = {
        "metadata": {
            "input_documents": input_docs,
            "persona": persona,
            "job_to_be_done": job_task,
            "processing_timestamp": datetime.now().isoformat(),
            "total_sections_analyzed": len(top_sections),
            "total_subsections_generated": len(subsections)
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }
    
    return output

def save_output(output: Dict, output_path: str):
    """Save output to JSON file"""
    try:
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nOutput saved to: {output_path}")
    
    except Exception as e:
        print(f"Error saving output: {e}")
        sys.exit(1)

def print_summary(output: Dict, processing_time: float):
    """Print processing summary"""
    
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    print(f"Processing time: {processing_time:.2f} seconds")
    print(f"Documents analyzed: {len(output['metadata']['input_documents'])}")
    print(f"Sections extracted: {len(output['extracted_sections'])}")
    print(f"Subsections generated: {len(output['subsection_analysis'])}")
    print(f"Persona: {output['metadata']['persona']}")
    print(f"Task: {output['metadata']['job_to_be_done']}")
    
    if output['extracted_sections']:
        print(f"\nTop 3 most relevant sections:")
        for i, section in enumerate(output['extracted_sections'][:3]):
            print(f"  {i+1}. {section['section_title']} (Page {section['page_number']})")

def main():
    """Main execution function"""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_json_path> <output_json_path>")
        print("Example: python main.py data/Collection_1/challenge1b_input.json data/Collection_1/challenge1b_output.json")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    print(f"Challenge 1B: Multi-Collection PDF Analysis")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # Step 1: Load input configuration
        print("Loading input configuration...")
        input_config = load_input_config(input_path)
        
        base_path = Path(input_path).parent
        persona = input_config['persona']['role']
        job_task = input_config['job_to_be_done']['task']
        
        print(f"Persona: {persona}")
        print(f"Task: {job_task}")
        print(f"Documents to process: {len(input_config['documents'])}")
        
        # Step 2: Process PDF documents
        print("\nProcessing PDF documents...")
        documents = process_documents(input_config['documents'], base_path)
        
        if not documents:
            print("Error: No documents could be processed")
            sys.exit(1)
        
        # Step 3: Analyze content and extract relevant sections
        top_sections, subsections = analyze_content(documents, persona, job_task)
        
        # Step 4: Generate output
        print("\nGenerating output...")
        output = generate_output(input_config, top_sections, subsections)
        
        # Step 5: Save output
        save_output(output, output_path)
        
        # Print summary
        processing_time = time.time() - start_time
        print_summary(output, processing_time)
        
        # Check processing time constraint
        if processing_time > 60:
            print(f"\nWarning: Processing took {processing_time:.2f}s, exceeding 60s constraint")
        else:
            print(f"\n✓ Processing completed within time constraint ({processing_time:.2f}s < 60s)")
    
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()