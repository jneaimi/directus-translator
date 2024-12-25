# Translation API Service

A FastAPI-based translation service that uses OpenAI's API to provide high-quality translations with a focus on Arabic language support.

## Features

- English to Arabic translation (extensible to other languages)
- Maintains original formatting and proper nouns
- Handles nested JSON structures
- Provides translation notes when necessary

## Prerequisites

- Python 3.8+
- OpenAI API key

## Installation

1. Clone the repository:

````bash
git clone <your-repository-url>
cd <repository-name>```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

## Running the Application

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

## API Usage

### Translate Endpoint

**POST** `/translate`

Request body example:
```json
{
  "payload": {
    "translations": {
      "greeting": "Hello, world!",
      "nested": {
        "message": "Welcome to our service"
      }
    }
  }
}
```

Response example:
```json
{
  "status": "success",
  "translated_data": {
    "payload": {
      "translations": {
        "greeting": "مرحباً بالعالم!",
        "nested": {
          "message": "مرحباً بكم في خدمتنا"
        }
      }
    }
  }
}
```

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
````
