# Customer Discovery Insights

An AI-powered tool that analyzes customer feedback and generates actionable product insights.

## Features

- Upload product context documents and customer transcripts
- AI-powered analysis using GPT-3.5
- Generate structured insights including:
  - Key Feature Recommendations
  - Product Requirements
  - User Objectives
  - User Journey Analysis
  - UX Considerations
  - Technical Requirements

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/customer-insights.git
cd customer-insights
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a .env file with your OpenAI API key:
```bash
OPENAI_API_KEY=your-api-key-here
```

4. Run the application:
```bash
python app.py
```

5. Open http://localhost:5004 in your browser

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key

## File Types Supported

- PDF (.pdf)
- Word Documents (.docx)
- Text Files (.txt)

## Dependencies

See requirements.txt for full list of dependencies:
- Flask
- OpenAI
- python-dotenv
- PyPDF2
- python-docx

## Security Notes

- Never commit your .env file
- Maximum file size: 16MB
- Files are processed in memory and not stored permanently
- Secure filename handling implemented

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
