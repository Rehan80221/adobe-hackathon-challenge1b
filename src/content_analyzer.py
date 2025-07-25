from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple
import re
from collections import Counter

class ContentAnalyzer:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize with lightweight sentence transformer model (90MB)"""
        self.model = SentenceTransformer(model_name)
        
        # Persona-specific keywords for enhanced relevance scoring
        self.persona_keywords = {
            'travel_planner': ['destination', 'itinerary', 'accommodation', 'attraction', 'transport', 'budget', 'activity', 'restaurant', 'hotel'],
            'hr_professional': ['form', 'onboarding', 'compliance', 'employee', 'policy', 'procedure', 'documentation', 'workflow', 'training'],
            'food_contractor': ['recipe', 'ingredient', 'vegetarian', 'buffet', 'cooking', 'menu', 'preparation', 'dietary', 'portion'],
            'researcher': ['methodology', 'analysis', 'data', 'literature', 'study', 'research', 'findings', 'conclusion'],
            'student': ['concept', 'theory', 'example', 'practice', 'exam', 'study', 'learning', 'explanation'],
            'analyst': ['trend', 'performance', 'metrics', 'analysis', 'comparison', 'data', 'insights', 'report']
        }
        
        # Task-specific keywords
        self.task_keywords = {
            'planning': ['plan', 'schedule', 'organize', 'prepare', 'arrange', 'coordinate'],
            'learning': ['learn', 'understand', 'study', 'practice', 'master', 'tutorial'],
            'analysis': ['analyze', 'evaluate', 'compare', 'assess', 'review', 'examine'],
            'preparation': ['prepare', 'create', 'make', 'develop', 'design', 'build']
        }

    def analyze_relevance(self, documents: List[Dict], persona: str, job_task: str) -> List[Dict]:
        """Analyze and score all sections based on persona and task relevance"""
        
        # Create enhanced query embedding
        query_text = self._create_enhanced_query(persona, job_task)
        query_embedding = self.model.encode([query_text])
        
        all_sections = []
        
        for doc in documents:
            if 'error' in doc:
                continue
                
            for section in doc['sections']:
                # Create enhanced section text for embedding
                section_text = self._enhance_section_text(section, persona, job_task)
                
                # Calculate semantic similarity
                section_embedding = self.model.encode([section_text])
                semantic_score = cosine_similarity(query_embedding, section_embedding)[0][0]
                
                # Calculate keyword relevance
                keyword_score = self._calculate_keyword_relevance(section, persona, job_task)
                
                # Calculate structural importance
                structural_score = self._calculate_structural_importance(section)
                
                # Combine scores with weights
                final_score = (
                    0.5 * semantic_score +           # Semantic similarity
                    0.3 * keyword_score +            # Keyword relevance  
                    0.2 * structural_score           # Structural importance
                )
                
                section_with_score = section.copy()
                section_with_score.update({
                    'document': doc['filename'],
                    'relevance_score': final_score,
                    'semantic_score': semantic_score,
                    'keyword_score': keyword_score,
                    'structural_score': structural_score,
                    'enhanced_text': section_text
                })
                
                all_sections.append(section_with_score)
        
        # Sort by relevance score
        return sorted(all_sections, key=lambda x: x['relevance_score'], reverse=True)

    def _create_enhanced_query(self, persona: str, job_task: str) -> str:
        """Create an enhanced query by combining persona, task, and relevant keywords"""
        
        # Extract persona type
        persona_type = self._extract_persona_type(persona.lower())
        
        # Get relevant keywords
        persona_kw = self.persona_keywords.get(persona_type, [])
        task_kw = self._extract_task_keywords(job_task.lower())
        
        # Combine everything
        enhanced_query = f"{persona} {job_task}"
        
        if persona_kw:
            enhanced_query += " " + " ".join(persona_kw[:5])  # Top 5 persona keywords
        
        if task_kw:
            enhanced_query += " " + " ".join(task_kw[:3])     # Top 3 task keywords
            
        return enhanced_query

    def _enhance_section_text(self, section: Dict, persona: str, job_task: str) -> str:
        """Enhance section text for better embedding by adding context"""
        
        base_text = f"{section['clean_title']} {section['content']}"
        
        # Add type context
        if section['type'] in ['chapter', 'major_heading', 'key_section']:
            base_text = f"Important section: {base_text}"
        
        return base_text[:1000]  # Limit length for processing efficiency

    def _extract_persona_type(self, persona: str) -> str:
        """Extract persona type from persona description"""
        persona_mappings = {
            'travel': 'travel_planner',
            'planner': 'travel_planner',
            'hr': 'hr_professional',
            'human resources': 'hr_professional',
            'food': 'food_contractor',
            'chef': 'food_contractor',
            'contractor': 'food_contractor',
            'researcher': 'researcher',
            'student': 'student',
            'analyst': 'analyst'
        }
        
        for key, value in persona_mappings.items():
            if key in persona:
                return value
        
        return 'general'  # Default fallback

    def _extract_task_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task description"""
        keywords = []
        
        for task_type, kw_list in self.task_keywords.items():
            for kw in kw_list:
                if kw in task:
                    keywords.extend(kw_list[:3])  # Add related keywords
                    break
        
        return list(set(keywords))  # Remove duplicates

    def _calculate_keyword_relevance(self, section: Dict, persona: str, job_task: str) -> float:
        """Calculate keyword-based relevance score"""
        
        text = f"{section['clean_title']} {section['content']}".lower()
        
        # Get relevant keyword sets
        persona_type = self._extract_persona_type(persona.lower())
        persona_keywords = self.persona_keywords.get(persona_type, [])
        task_keywords = self._extract_task_keywords(job_task.lower())
        
        # Count keyword matches
        persona_matches = sum(1 for kw in persona_keywords if kw in text)
        task_matches = sum(1 for kw in task_keywords if kw in text)
        
        # Normalize scores
        persona_score = min(persona_matches / max(len(persona_keywords), 1), 1.0)
        task_score = min(task_matches / max(len(task_keywords), 1), 1.0)
        
        # Combine with weights
        return 0.6 * persona_score + 0.4 * task_score

    def _calculate_structural_importance(self, section: Dict) -> float:
        """Calculate importance based on section structure and properties"""
        
        score = section.get('importance_score', 0.5)  # Base importance from PDF processor
        
        # Boost score based on section type
        type_boosts = {
            'chapter': 0.3,
            'major_heading': 0.2,
            'key_section': 0.25,
            'section': 0.15,
            'subsection': 0.1
        }
        
        score += type_boosts.get(section['type'], 0)
        
        # Adjust based on content length (moderate length is often better)
        word_count = section.get('word_count', 0)
        if 50 <= word_count <= 500:      # Sweet spot
            score += 0.1
        elif word_count < 20:            # Too short
            score -= 0.2
        elif word_count > 1000:          # Too long
            score -= 0.1
        
        return min(score, 1.0)  # Cap at 1.0

    def extract_subsections(self, top_sections: List[Dict], persona: str, job_task: str, max_subsections: int = 15) -> List[Dict]:
        """Extract meaningful subsections from top-ranked sections"""
        
        subsections = []
        
        for section in top_sections:
            content = section['content']
            
            # Split content into meaningful chunks
            chunks = self._split_content_intelligently(content)
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 30:  # Skip very short chunks
                    continue
                
                # Score this subsection
                subsection_text = f"{section['clean_title']}: {chunk}"
                chunk_embedding = self.model.encode([subsection_text])
                query_text = self._create_enhanced_query(persona, job_task)
                query_embedding = self.model.encode([query_text])
                
                relevance_score = cosine_similarity(query_embedding, chunk_embedding)[0][0]
                
                subsection = {
                    'document': section['document'],
                    'parent_section': section['clean_title'],
                    'content': chunk.strip(),
                    'page_number': section['page_number'],
                    'relevance_score': relevance_score,
                    'subsection_index': i
                }
                
                subsections.append(subsection)
        
        # Sort by relevance and return top subsections
        subsections.sort(key=lambda x: x['relevance_score'], reverse=True)
        return subsections[:max_subsections]

    def _split_content_intelligently(self, content: str) -> List[str]:
        """Split content into meaningful chunks based on sentences and structure"""
        
        # First try to split by paragraph markers
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would make chunk too long, save current and start new
            if len(current_chunk) + len(paragraph) > 300 and current_chunk:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += " " + paragraph
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # If we don't have good paragraph splits, fall back to sentence splitting
        if len(chunks) <= 1 and len(content) > 300:
            return self._split_by_sentences(content)
        
        return chunks

    def _split_by_sentences(self, content: str, target_length: int = 200) -> List[str]:
        """Split content by sentences when paragraph splitting doesn't work well"""
        
        sentences = re.split(r'[.!?]+\s+', content)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) > target_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def get_analysis_summary(self, sections: List[Dict]) -> Dict:
        """Generate analysis summary statistics"""
        
        if not sections:
            return {'error': 'No sections to analyze'}
        
        scores = [s['relevance_score'] for s in sections]
        
        return {
            'total_sections': len(sections),
            'avg_relevance_score': np.mean(scores),
            'max_relevance_score': np.max(scores),
            'min_relevance_score': np.min(scores),
            'score_distribution': {
                'high': len([s for s in scores if s > 0.7]),
                'medium': len([s for s in scores if 0.4 <= s <= 0.7]),
                'low': len([s for s in scores if s < 0.4])
            }
        }