# Ledger Management

Ledger Management is a Python-based financial ledger and data management system. It employs a data lake architecture (Bronze, Silver, and Gold layers) to ingest, process, and extract insights from financial data, including CSV, PDFs, and OFX files. It also includes capabilities to fetch real-time market data for investments.

## Features

- **Data Ingestion**: Processes and centralizes data from various sources (bank statements, CSVs, OFX).
- **Data Lake Architecture**:
  - Bronze: Raw data ingestion.
  - Silver: Cleaned and standardized data ready for processing.
  - Gold: Business insights, unified ledger, and reporting.
- **Market Data Integration**: Proof of concepts for integrating with APIs like YFinance and Alpha Vantage for stock and FII (Real Estate Investment Trust) quotes.

## Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package installer)

### Installation

1. Clone this repository:
   `ash
   git clone https://github.com/your-username/LedgerManagement.git
   cd LedgerManagement
   `

2. Create a virtual environment and activate it:
   `ash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/macOS:
   source venv/bin/activate
   `

3. Install the dependencies:
   `ash
   pip install -r requirements.txt
   `

4. Configure the environment variables:
   Copy the example environment file and configure your datalake folder paths.
   `ash
   cp .env.example .env
   `

## Usage

*Note: The project is actively under development.*

Run the main application:
`ash
python src/main.py
`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](LICENSE).
