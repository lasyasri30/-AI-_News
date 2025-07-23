from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer  # You can use LexRankSummarizer too

article_text = """
The ByteNews platform is designed to provide users with a personalized reading experience. 
Users can browse articles, search by category, and even generate summaries on demand. 
This allows them to quickly understand large content in a few seconds.
Future versions may include advanced NLP features and text-to-speech support.
"""

parser = PlaintextParser.from_string(article_text, Tokenizer("english"))
summarizer = LsaSummarizer()
summary = summarizer(parser.document, sentences_count=2)

print("🔹 Summary:")
for sentence in summary:
    print("-", sentence)
