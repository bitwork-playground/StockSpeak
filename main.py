from flask import Flask, request, jsonify
import requests
import yfinance as yf

app = Flask(__name__)


def search_logic(query):
    """
    Performs the search logic using the Yahoo Finance API.
    """
    if not query:
        return jsonify({"error": "A 'query' parameter is required."}), 400

    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Failed to fetch data from Yahoo Finance API: {e}"
        }), 502

    search_results = data.get('quotes', [])
    if not search_results:
        return jsonify([])

    # Limit the number of results to process to avoid long delays
    detailed_results = []
    for item in search_results[:10]:  # Process up to 10 results
        try:
            ticker = yf.Ticker(item['symbol'])
            info = ticker.info
            detailed_results.append({
                'name': item.get('longname', item.get('shortname')),
                'isin': info.get('isin'),
                'ticker': item.get('symbol'),
                'description': info.get('longBusinessSummary'),
                'type': item.get('quoteType'),
                'volume': info.get('averageVolume', 0)
            })
        except Exception:
            # Could fail if ticker info is not available, skip this result
            continue

    # Sort by volume in descending order
    detailed_results.sort(key=lambda x: x['volume'], reverse=True)

    return jsonify(detailed_results)


def price_logic(ticker_symbol):
    """
    Fetches price data for a given ticker.
    """
    if not ticker_symbol:
        return jsonify({"error": "A 'ticker' parameter is required."}), 400

    try:
        ticker = yf.Ticker(ticker_symbol)
        # Using 1y to get a year of historical data
        hist = ticker.history(period="1y")
        if hist.empty:
            return jsonify({
                "error": "Invalid ticker symbol or no data available."
            }), 404

        last_price = hist['Close'].iloc[-1]

        # Calculate percentage changes safely, using iloc for position-based
        # access
        change_1d = ((last_price - hist['Close'].iloc[-2]) /
                     hist['Close'].iloc[-2]) * 100 if len(hist) >= 2 else 0
        change_7d = ((last_price - hist['Close'].iloc[-6]) /
                     hist['Close'].iloc[-6]) * 100 if len(hist) >= 6 else 0
        change_30d = ((last_price - hist['Close'].iloc[-22]) /
                      hist['Close'].iloc[-22]) * 100 if len(hist) >= 22 else 0
        change_1y = ((last_price - hist['Close'].iloc[0]) /
                     hist['Close'].iloc[0]) * 100 if len(hist) > 1 else 0

        return jsonify({
            "ticker": ticker_symbol,
            "last_price": last_price,
            "change_1d_percent": f"{change_1d:.2f}%",
            "change_7d_percent": f"{change_7d:.2f}%",
            "change_30d_percent": f"{change_30d:.2f}%",
            "change_1y_percent": f"{change_1y:.2f}%",
        })

    except Exception as e:
        return jsonify({
            "error": "An error occurred processing "
                     f"ticker {ticker_symbol}: {e}"
        }), 500


def handler(request):
    """
    Main entry point for the cloud function.
    Routes requests to the appropriate handler based on the path.
    """
    path = request.path.strip('/')
    if path == 'search':
        return search(request)
    elif path == 'price':
        return price(request)
    else:
        return jsonify({
            "error": "Invalid endpoint. Please use /search or /price."
        }), 404


def search(request):
    """Handles the /search endpoint."""
    query = request.args.get('query')
    return search_logic(query)


def price(request):
    """Handles the /price endpoint."""
    ticker = request.args.get('ticker')
    return price_logic(ticker)


# This part is for local testing, it won't be used in Google Cloud Functions
if __name__ == '__main__':
    @app.route('/<path:path>', methods=['GET', 'POST'])
    def local_handler(path):
        return handler(request)

    app.run(host='0.0.0.0', port=8080, debug=True)
