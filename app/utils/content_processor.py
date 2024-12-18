import logging
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
import re
import io
from PyPDF2 import PdfReader
import ebooklib
from ebooklib import epub
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# Initialize NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""

    def extract_text_from_epub(self, file) -> str:
        """Extract text from EPUB file"""
        try:
            book = epub.read_epub(file)
            text = ""
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting EPUB text: {e}")
            return ""

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s.]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_important_sentences(self, text: str, num_sentences: int = 5) -> List[str]:
        """Extract most important sentences based on word frequency"""
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            
            # Remove stopwords and calculate word frequency
            word_freq = {}
            for word in words:
                if word.isalnum() and word not in self.stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Score sentences based on word importance
            sentence_scores = {}
            for sentence in sentences:
                score = 0
                words = word_tokenize(sentence.lower())
                for word in words:
                    if word.isalnum() and word not in self.stop_words:
                        score += word_freq.get(word, 0)
                sentence_scores[sentence] = score
            
            # Get top sentences
            important_sentences = sorted(sentence_scores.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:num_sentences]
            
            return [sentence[0] for sentence in important_sentences]
        except Exception as e:
            logger.error(f"Error extracting important sentences: {e}")
            return []

    def generate_summary(self, content: str, max_length: int = 1000) -> dict:
        """Generate a comprehensive summary using NLP techniques"""
        try:
            # Preprocess content
            cleaned_content = self.preprocess_text(content)
            
            # Get key sentences
            key_sentences = self.get_important_sentences(cleaned_content)
            
            # Extract main topics (most frequent meaningful words)
            words = word_tokenize(cleaned_content.lower())
            word_freq = {}
            for word in words:
                if word.isalnum() and word not in self.stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            main_topics = sorted(word_freq.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:5]
            
            # Create summary
            summary = " ".join(key_sentences)
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            return {
                'summary': summary,
                'key_sentences': key_sentences,
                'main_topics': [topic[0] for topic in main_topics],
                'full_text': cleaned_content
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                'summary': "Summary generation failed.",
                'key_sentences': [],
                'main_topics': [],
                'full_text': content
            }

    def create_summary_pdf(self, summary_data: dict, title: str = "Book Summary") -> bytes:
        """Create a PDF document with the summary"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph(title, title_style))
        
        # Main topics
        if summary_data['main_topics']:
            story.append(Paragraph("Main Topics:", styles['Heading2']))
            topics_text = ", ".join(summary_data['main_topics'])
            story.append(Paragraph(topics_text, styles['Normal']))
            story.append(Spacer(1, 20))

        # Summary
        story.append(Paragraph("Executive Summary:", styles['Heading2']))
        story.append(Paragraph(summary_data['summary'], styles['Normal']))
        story.append(Spacer(1, 20))

        # Key Sentences
        if summary_data['key_sentences']:
            story.append(Paragraph("Key Passages:", styles['Heading2']))
            for sentence in summary_data['key_sentences']:
                story.append(Paragraph(f"• {sentence}", styles['Normal']))
                story.append(Spacer(1, 10))

        doc.build(story)
        return buffer.getvalue() 