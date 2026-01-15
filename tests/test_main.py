import json
from unittest.mock import Mock, patch
import requests

import pandas as pd
import pytest
from flask import Flask, jsonify

from main import handler, price_logic, search_logic


# Fixture to create a Flask app context for tests
@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield


# --- Tests for search_logic ---


def test_search_logic_valid_query(app_context):
    """Test search logic with a valid query and mocked API responses."""
    mock_requests_get = Mock()
    mock_requests_get.return_value.json.return_value = {
        'quotes': [{
            'symbol': 'AAPL',
            'longname': 'Apple Inc.',
            'quoteType': 'EQUITY'
        }, {
            'symbol': 'TSLA',
            'longname': 'Tesla, Inc.',
            'quoteType': 'EQUITY'
        }]
    }
    mock_requests_get.return_value.raise_for_status = Mock()

    mock_yf_ticker = Mock()

    def ticker_side_effect(symbol):
        if symbol == 'AAPL':
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {
                'isin': 'US0378331005',
                'longBusinessSummary': 'Apple designs, manufactures, and '
                                       'markets consumer electronics.',
                'averageVolume': 90000000
            }
            return mock_ticker_instance
        if symbol == 'TSLA':
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {
                'isin': 'US88160R1014',
                'longBusinessSummary': 'Tesla designs, develops, '
                                       'manufactures, and sells '
                                       'electric vehicles.',
                'averageVolume': 150000000  # Higher volume
            }
            return mock_ticker_instance
        return Mock()

    mock_yf_ticker.side_effect = ticker_side_effect

    with patch('main.requests.get', mock_requests_get), \
            patch('main.yf.Ticker', mock_yf_ticker):
        response = search_logic('apple')
        data = json.loads(response.get_data(as_text=True))

        assert response.status_code == 200
        assert len(data) == 2
        # Tesla should be first due to higher volume
        assert data[0]['ticker'] == 'TSLA'
        assert data[1]['ticker'] == 'AAPL'
        assert data[0]['volume'] > data[1]['volume']


def test_search_logic_no_query(app_context):
    """Test search logic with no query provided."""
    response, status_code = search_logic('')
    assert status_code == 400
    data = json.loads(response.get_data(as_text=True))
    assert 'error' in data


def test_search_logic_api_error(app_context):
    """Test search logic when the external API returns an error."""
    mock_requests_get = Mock()
    mock_requests_get.return_value.raise_for_status.side_effect = \
        requests.exceptions.RequestException("API Error")

    with patch('main.requests.get', mock_requests_get):
        response, status_code = search_logic('error_query')
        assert status_code == 502
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


def test_search_logic_no_results(app_context):
    """Test search logic when the API returns no results."""
    mock_requests_get = Mock()
    mock_requests_get.return_value.json.return_value = {'quotes': []}
    mock_requests_get.return_value.raise_for_status = Mock()

    with patch('main.requests.get', mock_requests_get):
        response = search_logic('no_results_query')
        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert data == []


# --- Tests for price_logic ---


def test_price_logic_valid_ticker(app_context):
    """Test price logic with a valid ticker and mocked yfinance data."""
    mock_hist_data = pd.DataFrame({
        'Close': [100.0, 110.0, 105.0, 120.0, 125.0, 130.0] +
                 [150.0] * 20 + [160.0, 170.0]
    })

    mock_ticker = Mock()
    mock_ticker.history.return_value = mock_hist_data

    with patch('main.yf.Ticker', return_value=mock_ticker) as mock_yf:
        response = price_logic('AAPL')
        mock_yf.assert_called_with('AAPL')
        mock_ticker.history.assert_called_with(period='1y')

        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))
        assert data['ticker'] == 'AAPL'
        assert data['last_price'] == 170.0
        assert data['change_1d_percent'] == "6.25%"
        assert data['change_7d_percent'] == "13.33%"
        assert data['change_30d_percent'] == "13.33%"
        assert data['change_1y_percent'] == "70.00%"


def test_price_logic_no_ticker(app_context):
    """Test price logic with no ticker provided."""
    response, status_code = price_logic('')
    assert status_code == 400
    data = json.loads(response.get_data(as_text=True))
    assert 'error' in data


def test_price_logic_invalid_ticker(app_context):
    """Test price logic for an invalid ticker with no historical data."""
    mock_ticker = Mock()
    mock_ticker.history.return_value = pd.DataFrame()  # Empty dataframe

    with patch('main.yf.Ticker', return_value=mock_ticker):
        response, status_code = price_logic('INVALID')
        assert status_code == 404
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


def test_price_logic_yfinance_exception(app_context):
    """Test price logic when yfinance raises an exception."""
    with patch('main.yf.Ticker', side_effect=Exception("yfinance error")):
        response, status_code = price_logic('ERROR')
        assert status_code == 500
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data


# --- Tests for the main handler ---


@patch('main.search')
def test_handler_routes_to_search(mock_search, app_context):
    """Test that the handler correctly routes /search requests."""
    mock_search.return_value = jsonify({"message": "search called"}), 200

    mock_request = Mock()
    mock_request.path = '/search'

    response, status = handler(mock_request)
    assert status == 200
    data = json.loads(response.get_data(as_text=True))
    assert data['message'] == 'search called'
    mock_search.assert_called_once_with(mock_request)


@patch('main.price')
def test_handler_routes_to_price(mock_price, app_context):
    """Test that the handler correctly routes /price requests."""
    mock_price.return_value = jsonify({"message": "price called"}), 200

    mock_request = Mock()
    mock_request.path = '/price'

    response, status = handler(mock_request)
    assert status == 200
    data = json.loads(response.get_data(as_text=True))
    assert data['message'] == 'price called'
    mock_price.assert_called_once_with(mock_request)


def test_handler_invalid_path(app_context):
    """Test the handler's response to an invalid path."""
    mock_request = Mock()
    mock_request.path = '/invalid'

    response, status = handler(mock_request)
    assert status == 404
    data = json.loads(response.get_data(as_text=True))
    assert 'error' in data
