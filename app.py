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

        system_message = """You are a product analysis expert who provides concise, actionable insights.
        For each section, provide 3-5 unique, non-overlapping points. Each point should be specific to that section and not repeated elsewhere."""
        
        user_message = f"""
        Product Context:
        {product_text}

        Customer Transcript:
        {transcript_text}

        Analyze the customer transcript and provide insights in the following format. For each section, provide 3-5 UNIQUE points that are specific to that section:

        [KEY FEATURES]
        - (list unique feature recommendations)

        [PRODUCT REQUIREMENTS]
        - (list unique product requirements)

        [USER OBJECTIVES]
        - (list unique user objectives)

        [USER JOURNEY]
        - (list unique journey points)

        [UX CONSIDERATIONS]
        - (list unique UX points)

        [TECHNICAL REQUIREMENTS]
        - (list unique technical requirements)

        Ensure each point is unique and relevant to its specific section. Do not repeat information across sections.
        """

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
