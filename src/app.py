from flask import Flask, request, jsonify
from textblob import TextBlob

app = Flask(__name__)

def analyze_sentiment(text):
    """
    Analyze sentiment of text using TextBlob.
    
    Args:
        text (str): The review text to analyze
        
    Returns:
        dict: Contains sentiment label and polarity score
    """
    if not text or not text.strip():
        return {
            'sentiment': 'neutral',
            'polarity': 0.0,
            'message': 'Empty text provided'
        }
    
    # Create TextBlob object and get polarity
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    # Determine sentiment based on polarity score
    if polarity > 0.1:
        sentiment = 'positive'
    elif polarity < -0.1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'polarity': round(polarity, 3),
        'subjectivity': round(blob.sentiment.subjectivity, 3)
    }

@app.route('/analyze-review', methods=['POST'])
def analyze_review():
    """
    Endpoint to analyze sentiment of event reviews.
    
    Expected JSON payload:
        {
            "text": "The event was amazing and well organized!"
        }
    
    Returns:
        JSON response with sentiment analysis results
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided'
            }), 400
        
        # Extract text from request
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'error': 'No text field provided in request'
            }), 400
        
        # Analyze sentiment
        result = analyze_sentiment(text)
        
        return jsonify({
            'success': True,
            'text': text,
            'analysis': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)