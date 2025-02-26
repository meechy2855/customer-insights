import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import openai
from docx import Document
import PyPDF2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    """Extract text from a file based on its extension."""
    ext = file_path.rsplit('.', 1)[1].lower()
    
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == 'pdf':
            text = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            return ' '.join(text)
            
        elif ext == 'docx':
            doc = Document(file_path)
            return ' '.join(paragraph.text for paragraph in doc.paragraphs)
            
    except Exception as e:
        print(f"Error extracting text from {file_path}: {str(e)}")
        raise
        
    return ''

def analyze_with_openai(product_text, transcript_text):
    """Analyze texts using OpenAI API."""
    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")

        system_message = """You are a product analysis expert who provides distinct, non-overlapping insights for different aspects of product development.
        Each section must contain completely unique information that does not appear in any other section.
        
        - KEY FEATURES: Focus only on specific product features and capabilities
        - PRODUCT REQUIREMENTS: Focus only on business and functional requirements
        - USER OBJECTIVES: Focus only on user goals and what they want to achieve
        - USER JOURNEY: Focus only on the step-by-step flow of user interactions
        - UX CONSIDERATIONS: Focus only on interface and experience design elements
        - TECHNICAL REQUIREMENTS: Focus only on implementation and infrastructure needs
        
        Never repeat the same insight in multiple sections. Each point must be unique to its section."""
        
        user_message = f"""
        Product Context:
        {product_text}

        Customer Transcript:
        {transcript_text}

        Analyze the documents and provide strictly distinct insights for each section. Each insight must be unique and relevant only to its specific section:

        [KEY FEATURES]
        (List 3-4 specific product features and capabilities ONLY)

        [PRODUCT REQUIREMENTS]
        (List 3-4 business and functional requirements ONLY)

        [USER OBJECTIVES]
        (List 3-4 user goals and desired outcomes ONLY)

        [USER JOURNEY]
        (List 3-4 specific steps in the user's interaction flow ONLY)

        [UX CONSIDERATIONS]
        (List 3-4 interface and experience design elements ONLY)

        [TECHNICAL REQUIREMENTS]
        (List 3-4 implementation and infrastructure needs ONLY)

        IMPORTANT:
        1. Each section must contain completely different information
        2. Never mention the same concept in multiple sections
        3. If a point could fit in multiple sections, choose the most appropriate one and use different points for other sections
        4. Each bullet point should be a complete, specific insight
        5. Ensure each section focuses strictly on its designated aspect as defined above"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        return response.choices[0].message['content'].strip()
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if files are present
        if 'product_context' not in request.files or 'customer_transcript' not in request.files:
            return jsonify({'error': 'Missing required files'}), 400

        product_file = request.files['product_context']
        transcript_file = request.files['customer_transcript']

        # Validate files
        for file in [product_file, transcript_file]:
            if not file or not file.filename or not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Allowed types: txt, pdf, docx'}), 400

        # Save files
        product_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(product_file.filename))
        transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(transcript_file.filename))

        product_file.save(product_path)
        transcript_file.save(transcript_path)

        try:
            # Extract text from files
            product_text = extract_text(product_path)
            transcript_text = extract_text(transcript_path)

            # Analyze with OpenAI
            analysis = analyze_with_openai(product_text, transcript_text)

            return jsonify({'analysis': analysis})

        finally:
            # Clean up uploaded files
            for path in [product_path, transcript_path]:
                if os.path.exists(path):
                    os.remove(path)

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5004)
