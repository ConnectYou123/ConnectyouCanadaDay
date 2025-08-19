# Value Investing Stock Finder

A sophisticated Python application that scouts the internet to find publicly traded companies based on value investing principles from legendary investors like Warren Buffett, Charlie Munger, Benjamin Graham, and others.

## Features

- Analyzes companies based on 30 key value investing criteria
- Collects data from multiple reliable financial sources
- Performs comprehensive financial analysis
- Generates detailed reports on potential investment opportunities
- Implements various value investing strategies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-finder.git
cd stock-finder
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Required API Keys

The application requires the following API keys:
- Finnhub API key (for real-time market data)
- SEC-API key (for SEC filings data)

## Usage

### Web Interface (Recommended)

Run the web application:
```bash
python src/main.py
```

Then open your browser and navigate to: **http://localhost:3000**

The web interface provides:
- Interactive stock analysis dashboard
- Real-time progress tracking
- Detailed company information
- Downloadable reports
- RESTful API endpoints

### Command Line Interface

Run the command line version:
```bash
python src/web_app.py
```

## Project Structure

```
stock_finder/
├── src/
│   ├── data_collection/
│   │   ├── __init__.py
│   │   ├── financial_data.py
│   │   ├── market_data.py
│   │   └── sec_data.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── criteria.py
│   │   ├── screener.py
│   │   └── metrics.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── main.py
├── config/
│   └── config.py
├── tests/
│   └── __init__.py
├── requirements.txt
├── README.md
└── .env.example
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
