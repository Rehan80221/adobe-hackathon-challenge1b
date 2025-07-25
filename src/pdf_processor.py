import PyPDF2
import re
from typing import List, Dict, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

class PDFProcessor:
    def __init__(self):
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        self.stop_words = set(stopwords.words('english'))
        
        # Section detection patterns (order matters - more specific first)
        self.section_patterns = [
            (r'^Chapter\s+\d+[:\.]?\s*(.+)', 'chapter'),
            (r'^CHAPTER\s+\d+[:\.]?\s*(.+)', 'chapter'),
            (r'^\d+\.\d+\s+(.+)', 'subsection'),
            (r'^\d+\.\s+(.+)', 'section'),
            (r'^[A-Z][A-Z\s]{3,}$', 'major_heading'),
            (r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*:(.+)', 'titled_section'),
            (r'^(?:Introduction|Conclusion|Summary|Overview|Background)', 'key_section'),
        ]
        
        # Keywords that often indicate important sections
        self.importance_keywords = {
            'high': ['introduction', 'summary', 'conclusion', 'overview', 'key', 'important', 'main', 'primary'],
            'medium': ['method', 'approach', 'procedure', 'process', 'technique', 'strategy'],
            'contextual': ['example', 'case', 'illustration', 'demonstration']
        }

    def extract_text_with_structure(self, pdf_path: str) -> Dict:
        """Extract text while preserving page numbers and section structure"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                pages_content = []
                full_text = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            pages_content.append({
                                'page_number': page_num,
                                'text': page_text,
                                'clean_text': self._clean_text(page_text)
                            })
                            full_text += page_text + "\n"
                    except Exception as e:
                        print(f"Error extracting page {page_num}: {e}")
                        continue
                
                # Identify sections across all pages
                sections = self._identify_sections(pages_content)
                
                return {
                    'filename': pdf_path.split('/')[-1],
                    'total_pages': len(pages_content),
                    'pages': pages_content,
                    'sections': sections,
                    'full_text': full_text
                }
                
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return {
                'filename': pdf_path.split('/')[-1],
                'total_pages': 0,
                'pages': [],
                'sections': [],
                'full_text': '',
                'error': str(e)
            }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\-\(\)]', ' ', text)
        # Remove page numbers and common PDF artifacts
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text)
        return text.strip()

    def _identify_sections(self, pages_content: List[Dict]) -> List[Dict]:
        """Identify section boundaries and titles across all pages"""
        sections = []
        current_section = None
        
        for page in pages_content:
            lines = page['clean_text'].split('\n')
            page_num = page['page_number']
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # Check if line matches any section pattern
                section_match = self._match_section_pattern(line)
                
                if section_match:
                    # Save previous section if exists
                    if current_section:
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'title': section_match['title'],
                        'type': section_match['type'],
                        'page_number': page_num,
                        'start_line': line_num,
                        'content': '',
                        'importance_score': self._calculate_importance_score(section_match['title'])
                    }
                elif current_section:
                    # Add content to current section
                    current_section['content'] += line + ' '
                else:
                    # No current section, create a default one
                    if not sections:  # First content without a clear section
                        current_section = {
                            'title': f'Introduction - Page {page_num}',
                            'type': 'content',
                            'page_number': page_num,
                            'start_line': line_num,
                            'content': line + ' ',
                            'importance_score': 0.5
                        }
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        # Post-process sections
        return self._post_process_sections(sections)

    def _match_section_pattern(self, line: str) -> Dict:
        """Check if line matches any section pattern"""
        for pattern, section_type in self.section_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                if match.groups():
                    title = match.group(1).strip()
                else:
                    title = line.strip()
                
                return {
                    'title': title,
                    'type': section_type,
                    'pattern': pattern
                }
        
        # Check for implicit sections (lines that look like headings)
        if self._looks_like_heading(line):
            return {
                'title': line.strip(),
                'type': 'implicit_heading',
                'pattern': 'implicit'
            }
        
        return None

    def _looks_like_heading(self, line: str) -> bool:
        """Heuristic to identify lines that look like headings"""
        line = line.strip()
        
        # Too short or too long
        if len(line) < 3 or len(line) > 100:
            return False
        
        # Ends with period (likely not a heading)
        if line.endswith('.'):
            return False
        
        # Contains many common words (likely paragraph text)
        words = word_tokenize(line.lower())
        common_words = sum(1 for word in words if word in self.stop_words)
        if len(words) > 0 and common_words / len(words) > 0.5:
            return False
        
        # Capitalization patterns
        words = line.split()
        if len(words) <= 5 and sum(1 for word in words if word[0].isupper()) >= len(words) * 0.6:
            return True
        
        return False

    def _calculate_importance_score(self, title: str) -> float:
        """Calculate importance score based on title content"""
        title_lower = title.lower()
        score = 0.5  # Base score
        
        # Check for high importance keywords
        for keyword in self.importance_keywords['high']:
            if keyword in title_lower:
                score += 0.3
        
        # Check for medium importance keywords
        for keyword in self.importance_keywords['medium']:
            if keyword in title_lower:
                score += 0.2
        
        # Check for contextual keywords
        for keyword in self.importance_keywords['contextual']:
            if keyword in title_lower:
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0

    def _post_process_sections(self, sections: List[Dict]) -> List[Dict]:
        """Post-process sections to improve quality"""
        processed_sections = []
        
        for section in sections:
            # Clean up content
            content = section['content'].strip()
            if len(content) < 10:  # Skip very short sections
                continue
            
            # Limit content length for processing efficiency
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            # Create word count and sentence count
            words = word_tokenize(content)
            sentences = sent_tokenize(content)
            
            processed_section = section.copy()
            processed_section.update({
                'content': content,
                'word_count': len(words),
                'sentence_count': len(sentences),
                'clean_title': self._clean_text(section['title'])
            })
            
            processed_sections.append(processed_section)
        
        return processed_sections

    def get_document_summary(self, processed_doc: Dict) -> Dict:
        """Generate a summary of the processed document"""
        return {
            'filename': processed_doc['filename'],
            'total_pages': processed_doc['total_pages'],
            'total_sections': len(processed_doc['sections']),
            'section_types': list(set(s['type'] for s in processed_doc['sections'])),
            'avg_section_length': sum(s['word_count'] for s in processed_doc['sections']) / max(len(processed_doc['sections']), 1)
        }