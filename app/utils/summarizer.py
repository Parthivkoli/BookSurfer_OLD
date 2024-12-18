from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize.treebank import TreebankWordDetokenizer
from collections import defaultdict
from heapq import nlargest
from transformers import pipeline
import nltk
import re

class TextSummarizer:
    def __init__(self):
        # Download all required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
        except Exception as e:
            print(f"Error downloading NLTK data: {e}")
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = set()  # Fallback to empty set if stopwords fail
            
        self.detokenizer = TreebankWordDetokenizer()
        
        # Initialize transformers pipeline with error handling
        try:
            self.abstractive_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception as e:
            print(f"Error loading abstractive summarizer: {e}")
            self.abstractive_summarizer = None

    def clean_text(self, text):
        if not text:
            return ""
        # Remove special characters and extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?]', '', text)
        return text.strip()

    def extractive_summarize(self, text, length='medium'):
        if not text:
            return "No text provided for summarization."
            
        try:
            # Basic sentence splitting if NLTK fails
            if '.' not in text:
                return text[:500] + "..."  # Return first 500 chars if no sentences
                
            # Try NLTK tokenization, fall back to basic split if it fails
            try:
                sentences = sent_tokenize(text)
            except Exception:
                sentences = [s.strip() for s in text.split('.') if s.strip()]
                
            if not sentences:
                return text[:500] + "..."
                
            # Simple word tokenization if NLTK fails
            try:
                words = word_tokenize(text.lower())
            except Exception:
                words = text.lower().split()
            
            # Remove stop words if available
            word_tokens = [word for word in words 
                         if word not in self.stop_words and word.isalnum()]
            
            # Calculate word frequency
            freq = FreqDist(word_tokens)
            
            # Score sentences
            scores = defaultdict(int)
            for i, sentence in enumerate(sentences):
                for word in sentence.lower().split():
                    if word in freq:
                        scores[i] += freq[word]
            
            # Determine summary length
            length_ratio = {
                'short': 0.2,
                'medium': 0.3,
                'long': 0.5
            }
            num_sentences = max(1, int(len(sentences) * length_ratio.get(length, 0.3)))
            
            # Get top sentences
            top_sentences = nlargest(num_sentences, scores, key=scores.get)
            top_sentences.sort()
            
            summary = ' '.join([sentences[i] for i in top_sentences])
            return summary if summary else text[:500] + "..."
            
        except Exception as e:
            print(f"Error in extractive summarization: {e}")
            return text[:500] + "..."  # Fallback to simple truncation

    def abstractive_summarize(self, text, length='medium'):
        if not self.abstractive_summarizer:
            return self.extractive_summarize(text, length)
            
        try:
            max_length = {
                'short': 130,
                'medium': 250,
                'long': 400
            }
            min_length = {
                'short': 30,
                'medium': 100,
                'long': 200
            }
            
            # Handle text length limitations
            if len(text) > 1024:
                text = text[:1024]  # Truncate to avoid model limitations
                
            summary = self.abstractive_summarizer(
                text,
                max_length=max_length.get(length, 250),
                min_length=min_length.get(length, 100),
                do_sample=False
            )[0]['summary_text']
            return summary
        except Exception as e:
            print(f"Error in abstractive summarization: {e}")
            return self.extractive_summarize(text, length)

    def summarize(self, text, method='extractive', length='medium'):
        cleaned_text = self.clean_text(text)
        
        if not cleaned_text:
            return "No text provided for summarization."
        
        try:
            if method == 'abstractive' and self.abstractive_summarizer:
                return self.abstractive_summarize(cleaned_text, length)
            else:
                return self.extractive_summarize(cleaned_text, length)
        except Exception as e:
            print(f"Error in summarization: {e}")
            return "An error occurred during summarization. Please try again."