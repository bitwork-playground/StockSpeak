# Yahoo Finance Proxy - Google Cloud Function

This project provides a simple, serverless proxy that uses a Google Cloud Function to expose two endpoints from the Yahoo Finance API. The endpoints allow you to search for stocks and ETFs and retrieve their latest price data.

## Features

- **Search Endpoint (`/search`)**: Search for financial instruments by name, ticker, ISIN, or description.
- **Price Endpoint (`/price`)**: Get the latest price and recent performance data for a specific ticker.
- **Serverless**: Deployed as a Google Cloud Function for easy scaling and management.
- **Validated**: Includes a full suite of unit tests and linting to ensure code quality.

## Endpoints

### `/search`

- **Method**: `GET`
- **Query Parameters**:
  - `query` (required): The search term to look for.
- **Success Response** (`200 OK`):
  - A JSON array of matching stocks, sorted by trading volume.
  - Example: `GET /search?query=tesla`
    ```json
    [
      {
        "name": "Tesla, Inc.",
        "isin": "US88160R1014",
        "ticker": "TSLA",
        "description": "Tesla, Inc. designs, develops, manufactures, and sells electric vehicles...",
        "type": "EQUITY",
        "volume": 150000000
      }
    ]
    ```
- **Error Responses**:
  - `400 Bad Request`: If the `query` parameter is missing.
  - `502 Bad Gateway`: If the Yahoo Finance API is unavailable.

### `/price`

- **Method**: `GET`
- **Query Parameters**:
  - `ticker` (required): The stock ticker to look up.
- **Success Response** (`200 OK`):
  - A JSON object with the latest price and percentage changes.
  - Example: `GET /price?ticker=AAPL`
    ```json
    {
      "ticker": "AAPL",
      "last_price": 170.0,
      "change_1d_percent": "6.25%",
      "change_7d_percent": "13.33%",
      "change_30d_percent": "13.33%",
      "change_1y_percent": "70.00%"
    }
    ```
- **Error Responses**:
  - `400 Bad Request`: If the `ticker` parameter is missing.
  - `404 Not Found`: If the ticker is invalid or has no data.
  - `500 Internal Server Error`: If an unexpected error occurs.

## Deployment

### Prerequisites

1.  **Google Cloud SDK**: Make sure you have the `gcloud` CLI installed and authenticated.
2.  **Project ID**: Have your Google Cloud Project ID ready.
3.  **Permissions**: Ensure your account has the necessary permissions to deploy Cloud Functions.

### Steps

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Configure the Deployment Script**:
    - Open the `deploy.sh` script.
    - Set the `PROJECT_ID` variable to your Google Cloud Project ID.
    - (Optional) Customize the `FUNCTION_NAME` and `REGION` if needed.

3.  **Run the Deployment Script**:
    ```bash
    chmod +x deploy.sh
    ./deploy.sh
    ```

4.  **Verify the Deployment**:
    - After the script finishes, it will output the URL of your deployed function.
    - You can test the endpoints using a tool like `curl` or your browser:
      ```bash
      # Test the search endpoint
      curl "<your-function-url>/search?query=google"

      # Test the price endpoint
      curl "<your-function-url>/price?ticker=GOOGL"
      ```

## Local Development and Testing

To run the function locally or run the tests, follow these steps:

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt -r tests/test_requirements.txt
    ```

2.  **Run the Linter**:
    ```bash
    flake8 main.py tests/test_main.py
    ```

3.  **Run the Unit Tests**:
    ```bash
    PYTHONPATH=. pytest
    ```
