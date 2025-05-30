# -*- coding: utf-8 -*-
"""PDD_stock_analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WQapnlpe1vIMoneHvvnV8UrQCFKyW35y
"""

import pandas as pd
import numpy as np
import pandas as pd
from datetime import date
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar

"""**Valuation**

Determine the company value using the capital asset pricing model (CAPM) and the
dividend growth model. For CAPM, you may use the Beta value indicated on Yahoo Finance
(please indicate the date the Beta value was taken).
"""

# Function to get the current 10-Year Treasury Yield (Risk-Free Rate)
def get_risk_free_rate():
    """Get current 10-Year Treasury Yield with robust type handling"""
    try:
        tnx = yf.Ticker("^TNX")
        rf_data = tnx.history(period="1d")

        if not rf_data.empty:
            rate = float(rf_data['Close'].iloc[-1]) / 100
            print(f"Using current Treasury yield from Yahoo: {rate:.2%}")
            return rate

        raise ValueError("No current data available")

    except Exception as e:
        print(f"Error fetching risk-free rate: {str(e)}")
        print("Using fallback rate 4.17%")
        return 0.0417  # Fallback rate

# Set parameters
market_index = "^GSPC"
ticker = "PDD"
start_date = "2020-03-11"
end_date = "2025-03-12"

# Get the risk-free rate
risk_free_rate = get_risk_free_rate()

# Download historical data
data = yf.download([ticker, market_index], start=start_date, end=end_date)['Close']

# Reshape the data
df = data.reset_index().melt(id_vars='Date', var_name='Ticker', value_name='Price')
df = df.pivot(index='Date', columns='Ticker', values='Price').dropna()

# Use 'ME' for month-end frequency to avoid the FutureWarning
monthly_returns = df.resample('ME').ffill().pct_change().dropna()
monthly_returns.columns = ['Market Return', 'Stock Return']

# Calculate covariance matrix
covariance_matrix = np.cov(monthly_returns['Stock Return'], monthly_returns['Market Return'])

# Beta calculation
beta = covariance_matrix[0, 1] / covariance_matrix[1, 1]

# Annualize the monthly market return
market_return_annualized = monthly_returns['Market Return'].mean() * 12

# CAPM formula
expected_return = risk_free_rate + beta * (market_return_annualized - risk_free_rate)

# Output the results
print(f"\nCAPM Analysis for {ticker} ")
print("="*40)
print(f"Data Period: {df.index[0].date()} to {df.index[-1].date()}")
print(f"Risk-Free Rate: {risk_free_rate:.2%}")
print(f"Beta: {beta:.4f}")
print(f"Expected Return (CAPM): {expected_return:.2%}")

"""**Technical Analysis & Monte Carlo Simulation**

Perform technical analysis in Python on the 2024 values stock. Create
the Bollinger Bands for the stock. Also perform Monte Carlo simulation on the stock. Develop the
simulation using stock prices from January 1, 2024, through December 31, 2024, and simulate the
stock price for January 1, 2025, through December 31, 2025.  Perform 10,000 simulations and
calculate the average and standard deviation of the return on the stock.
"""

# Download stock data
data = yf.download(ticker, start=start_date, end=end_date)

# Flatten MultiIndex columns
data.columns = [col[0].lower() if col[0] != '' else 'date' for col in data.columns]

# Optional: reset index if needed
data.reset_index(inplace=True)

# Extract 2024 data
data['Date'] = pd.to_datetime(data['Date'])
data_2024 = data[data['Date'].dt.year == 2024]

# Drop the 'volume' column
data = data.drop(columns=['volume'])

import matplotlib.pyplot as plt

def plot_standard_bollinger_bands(df, window=30, title='Bollinger Bands - PDD 2024' ,show_every_month=True):
    # Sort by Date
    df = df.sort_values(by='Date').reset_index(drop=True)

    # Rolling calculations
    df[f'MA{window}'] = df['close'].rolling(window=window).mean()
    df[f'STD{window}'] = df['close'].rolling(window=window).std()
    df['Upper'] = df[f'MA{window}'] + (2 * df[f'STD{window}'])
    df['Lower'] = df[f'MA{window}'] - (2 * df[f'STD{window}'])

    # Prepare the valid Bollinger Band area part
    bollinger_area = df.dropna(subset=['Upper', 'Lower']).reset_index(drop=True)

    # Plotting
    plt.figure(figsize=(14, 7))

    # Plot full Close Price and Moving Average
    plt.plot(df['Date'], df['close'], label='Close Price', color='blue')
    plt.plot(df['Date'], df[f'MA{window}'], label=f'{window}-Day MA', color='orange')

    # Plot Bollinger Bands (only the shaded area where available)
    plt.plot(df['Date'], df['Upper'], label='Upper Band', color='green')
    plt.plot(df['Date'], df['Lower'], label='Lower Band', color='red')

    # Fill only where bands are valid
    plt.fill_between(bollinger_area['Date'], bollinger_area['Upper'], bollinger_area['Lower'], color='grey', alpha=0.1)

    # Set major ticks to each month and format the date as 'Jan', 'Feb', etc.
    ax = plt.gca()
    if show_every_month == True:
        ax.xaxis.set_major_locator(mdates.MonthLocator())  # Force every month to show
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))  # 'Jan 2024' format


    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Close Price (USD)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

plot_standard_bollinger_bands(data_2024, window=30)

# Year prediction

# Extract and Transform the data
data_close = data[['Date','close']]
data_close = data_close.sort_values(by='Date', ascending=False).reset_index(drop=True)
data_close['Date'] = pd.to_datetime(data_close['Date'])  # Ensure 'Date' is datetime
data_close = data_close[(data_close['Date'] >= '2024-01-01') & (data_close['Date'] <= '2024-12-31')]
data_close['close'] = pd.to_numeric(data_close['close'])

# Estimate the Close difference and the mean, std, var and drift of it.
data_close['Diff Close'] = np.log(data_close['close'] / data_close['close'].shift(-1))

mean = data_close['Diff Close'].mean()
std = data_close['Diff Close'].std()
var = data_close['Diff Close'].var()

drift = mean - var/2

# Calculate future dates for the year
start_price = data_close['close'].iloc[-1]

# Generate business days for 2025 (approx. 252 trading days)
start_date = '2025-01-01'
end_date = '2025-12-31'

us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
business_days = pd.date_range(start='2025-01-01', end='2025-12-31', freq=us_bd)

# Simulate stock prices using GBM
np.random.seed(42)  # for reproducibility
simulated_prices = [start_price]

for _ in range(len(business_days)-1):
    random_shock = np.random.normal()
    price = simulated_prices[-1] * np.exp(drift + std * random_shock)
    simulated_prices.append(price)

# Create DataFrame for 2025 simulated prices
simulated_2025 = pd.DataFrame({
    'Date': business_days,
    'Simulated_Close': simulated_prices
})

# Rename simulated column to 'Close' for consistency
simulated_2025 = simulated_2025.rename(columns={'Simulated_Close': 'Close'})

# Select only 'Date' and 'Close' columns from actual 2024 data
actual_2024 = data_close[['Date', 'close']]

# Concatenate 2024 actual and 2025 simulated data
combined_df = pd.concat([actual_2024, simulated_2025], ignore_index=True)
combined_df = combined_df.sort_values(by='Date').reset_index(drop=True)

plot_standard_bollinger_bands(combined_df, window=30,title='Bollinger Bands - PDD 2024 - 2025' ,show_every_month=False)

# 10000 thousand scenarios

# Parameters from your historical 2024 data
mean = data_close['Diff Close'].mean()
std = data_close['Diff Close'].std()
var = data_close['Diff Close'].var()
drift = mean - (0.5 * var)

# Starting price = last close of 2024
start_price = data_close['close'].iloc[-1]

n_simulations = 10_000
random_shocks = np.random.normal(loc=0, scale=1, size=n_simulations)

# Simulate prices for Jan 2, 2025
jan_2_prices = start_price * np.exp(drift + std * random_shocks)

# Compute returns
returns = (jan_2_prices - start_price) / start_price  # Relative gain/loss

# Compute statistics
avg_gain_loss = returns.mean()
std_dev = returns.std()

print(f"Average Gain/Loss: {avg_gain_loss :.2%}")
print(f"Standard Deviation: {std_dev:.2%}")

"""**Stock Signals **

Identify the buy and sell signals for the stock from January 1, 2024, through December 31,
2024, using Simple Moving Average and Exponential Moving Average techniques. For both
cases, use 30 days for the short-term moving average and 90 days for the long-term moving
average.
"""

# Simple Moving Average (SMA) and Exponential Moving Average (EMA)
sma_30 = data_2024['close'].rolling(window=30).mean()
data_2024['SMA_30'] = sma_30

ema_90 = data_2024['close'].ewm(span=90, adjust=False).mean()
data_2024['EMA_90'] = ema_90

# Buy Sell Signals
data_2024['Signal'] = 0
data_2024['Signal'] = np.where(data_2024['SMA_30'] > data_2024['EMA_90'], 1, 0)

# Create Position
data_2024['Position'] = data_2024['Signal'].diff()

# Convert 'Date' column to datetime format
data_2024['Date'] = pd.to_datetime(data_2024['Date'])

# Set 'Date' as the index
data_2024.set_index('Date', inplace=True)

plt.figure(figsize=(25, 10))

# Plot close price, short-term and long-term moving averages
plt.plot(data_2024.index, data_2024['close'], color='black', label='Close Price', linewidth=2)
plt.plot(data_2024.index, data_2024['SMA_30'], color='blue', label='SMA 30-day', linewidth=2, linestyle="dashed")
plt.plot(data_2024.index, data_2024['EMA_90'], color='green', label='EMA 90-day', linewidth=2, linestyle="dashdot")

# Plot ‘BUY’ signals
plt.scatter(data_2024[data_2024['Position'] == 1].index,
            data_2024['SMA_30'][data_2024['Position'] == 1],
            marker='^', color='green', label='BUY Signal', s=150, edgecolors='black', zorder=3)

# Plot ‘SELL’ signals
plt.scatter(data_2024[data_2024['Position'] == -1].index,
            data_2024['EMA_90'][data_2024['Position'] == -1],
            marker='v', color='red', label='SELL Signal', s=150, edgecolors='black', zorder=3)

# Labels and title
plt.ylabel('Price in USD', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.title('PDD Stock Price with SMA & EMA Trading Signals', fontsize=16, fontweight='bold')

# Grid and legend
plt.legend(fontsize=12)
plt.grid(True, linestyle="--", alpha=0.6)

# Format x-axis to show month and year properly
ax = plt.gca()
ax.xaxis.set_major_locator(mdates.MonthLocator())  # One tick per month
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))  # Format: Jan 2024
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

"""**Forecasting **

Using Facebook Prophet, generate a prediction of the stock price. Use January 1, 2024,
through December 31, 2024, to create the model, then create the projection for January 1, 2025,
through December 31, 2025.
"""

# Reset index to turn the datetime index into a column
data_2024 = data_2024.reset_index()

# Rename the column from 'Date' to 'date' (if needed)
data_2024.rename(columns={'Date': 'date'}, inplace=True)
data_2024

from prophet import Prophet

data_2024.columns=data_2024.columns.str.replace('close', 'y', regex=False)
data_2024.columns=data_2024.columns.str.replace('date', 'ds', regex=False)

stock_symbol = "PDD"
data_prophet = data_2024[['ds', 'y']]

# Initialize the Prophet model
base_model = Prophet()

# Fit the model
base_model.fit(data_prophet)

# Create a dataframe for future dates
future = base_model.make_future_dataframe(periods=365)  # Predict for the next 365 days and by default it will predict daily prices

# Make predictions
forecast_2025 = base_model.predict(future)

# Step 6: Plot Forecast
base_model.plot(forecast_2025)
plt.title(f"Baseline model for {stock_symbol} Stock Price Forecast")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.show()

# # Step 7: Plot Components (Trend & Seasonality)
base_model.plot_components(forecast_2025)
plt.show()

"""The baseline model projects a steady decline in PDD stock prices throughout 2025, with uncertainty intervals widening substantially after March 2025—indicating growing volatility or reduced forecast confidence. The trend component in the decomposition plot mirrors this downward movement, reinforcing the model's core prediction. The weekly seasonality plot shows a distinctive U-shaped curve: predicted values are higher on Sundays and Saturdays, and dip from Monday to Friday. This pattern suggests relatively stronger model-predicted activity on weekends, though this may reflect residual seasonality patterns rather than actual trading behavior, since PDD stock is typically traded on weekdays through standard exchanges.

Adjusting the Hyperparameters

seasonality_mode='multiplicative' was chosen to better capture percentage-based fluctuations in stock prices, as opposed to the additive mode which assumes constant absolute changes—less suitable for volatile assets like equities.

Enabling both yearly and weekly seasonality helps capture repeating market patterns and reduces residual variation in the model:

yearly_seasonality=13 adjusts the frequency and amplitude of long-term cycles. A value too high can lead to overfitting, while too low smooths out legitimate seasonal patterns.

Using add_seasonality to explicitly define and control seasonality components is often more effective than relying on Prophet’s default weekly_seasonality=True. For PDD stock, this approach reflects more realistic trading patterns that vary by weekday.

Country holidays have a significant impact on stock market activity. To improve accuracy, the model should incorporate China and U.S. market holidays, especially considering PDD is a U.S.-listed Chinese company. This can include:

Full and early market closures

U.S. stock market holidays (e.g., Thanksgiving, Independence Day)

Company-specific events such as earnings release dates or investor announcements, which can be modeled as custom or conditional holidays.
"""

from prophet.make_holidays import make_holidays_df

# Ensure the 'Date' column is renamed to 'ds' for compatibility with Prophet
h_data =data_2024[['ds']]

# # create the year list
year_list = h_data['ds'].dt.year.unique().tolist()

Stock_mkt_holidays = make_holidays_df(year_list=year_list,country='US')
Stock_mkt_holidays.head()

# include seasonality of stock exchange holidays and early close days for 2024 and 2025

New_Years = pd.DataFrame({'holiday': 'New Years Day','ds': pd.to_datetime(['2024-01-01', '2025-01-01'])})
Martin_Luther = pd.DataFrame({'holiday': 'Martin Luther King Jr. Day','ds': pd.to_datetime(['2024-01-15', '2025-01-20'])})
Presidents_Day = pd.DataFrame({'holiday': 'Presidents Day','ds': pd.to_datetime(['2024-02-19', '2025-02-17'])})
Good_Friday = pd.DataFrame({'holiday': 'Good Friday','ds': pd.to_datetime(['2024-03-29', '2025-04-25'])})
Memorial_Day = pd.DataFrame({'holiday': 'Memorial Day','ds': pd.to_datetime(['2024-05-27', '2025-05-26'])})
Juneteenth_Day = pd.DataFrame({'holiday': 'Juneteenth National Independence Day','ds': pd.to_datetime(['2024-06-19', '2025-06-19'])})
Independence_Day= pd.DataFrame({'holiday': 'Independence Day','ds': pd.to_datetime(['2024-07-04', '2025-07-04'])})
Labor_Day= pd.DataFrame({'holiday': 'Labor Day','ds': pd.to_datetime(['2024-09-02', '2025-09-01'])})
Thanksgiving_Day= pd.DataFrame({'holiday': 'Thanksgiving Day','ds': pd.to_datetime(['2024-11-28', '2025-11-27'])})
Christmas_Day= pd.DataFrame({'holiday': 'Christmas Day','ds': pd.to_datetime(['2024-12-25', '2025-12-25'])})

# Including early close days
before_Independence_Day = pd.DataFrame({'holiday':'before Independence Day', 'ds': pd.to_datetime(['2024-07-03','2025-07-03'])})
day_after_Thanksgiving = pd.DataFrame({'holiday':'day after Thanksgiving', 'ds': pd.to_datetime(['2024-11-29','2025-11-28'])})
Christmas_Eve = pd.DataFrame({'holiday':'Christmas Eve', 'ds': pd.to_datetime(['2024-12-24','2025-12-24'])})

# To include seasonality of earning announcements for MRK that is before 2 weeks (7*14)  and after 4 weeks (7*4)
earnings_reported_dates = pd.DataFrame({'holiday':'Earning releases', 'ds': pd.to_datetime(['2024-04-25','2024-07-30','2024-10-31','2025-02-04', '2025-04-24']),'lower_window': -14,'upper_window': 28})

# concatenate the holidays, early closing days and MRK earning announcement

holidays = pd.concat([
	Stock_mkt_holidays,
	New_Years,
	Martin_Luther,
	Presidents_Day,
	Good_Friday,
	Memorial_Day,
	Juneteenth_Day,
	Independence_Day,
	Labor_Day,
	Thanksgiving_Day,
	Christmas_Day,
    before_Independence_Day,
    day_after_Thanksgiving,
    Christmas_Eve,
    earnings_reported_dates,
]).sort_values('ds').reset_index(drop=True)

stock_symbol = "PDD"

# Tuning the Prophet model
model_1 = Prophet(seasonality_mode='multiplicative', yearly_seasonality=15, weekly_seasonality=False, holidays=holidays)
model_1.add_seasonality(name='weekly',period=7, fourier_order=4,prior_scale=0.01)

# Fit the model
model_1.fit(data_prophet)

# Create a dataframe for future dates
future = model_1.make_future_dataframe(periods=365)  # Predict for the next 365 days and by default it will predict daily prices

# Make predictions
forecast_2025 = model_1.predict(future)

# Step 6: Plot Forecast
model_1.plot(forecast_2025)
plt.title(f"{stock_symbol} Stock Price Forecast")
plt.xlabel("Date")
plt.ylabel("Close Price")
plt.show()

# # Step 7: Plot Components (Trend & Seasonality)
model_1.plot_components(forecast_2025)
plt.show()

"""We can see the line crosses most of the actual data (black dots) compared to the previous graph, where it struggles to data points given it was too generalised. Also, the holiday graph's variation ranges from negative 5 to positive 4."""

# Extract 2024 and 2025 actual data
act24_2025 = data[(data['Date'] >= '2024-01-01') & (data['Date'] <= '2025-03-11')]
act24_2025.columns=act24_2025.columns.str.replace('close', 'y', regex=False)
act24_2025.columns=act24_2025.columns.str.replace('Date', 'ds', regex=False)
actual_data = act24_2025[['ds', 'y']]

predict_2025 = forecast_2025[(forecast_2025['ds'] >= '2024-01-01') & (forecast_2025['ds'] <= '2025-03-11')][['ds', 'yhat']]
predict_2025

plt.figure(figsize=(12, 6))

# Plot actual close prices
plt.plot(actual_data['ds'], actual_data['y'], label='Actual Close Price', color='blue')

# Plot forecasted prices
plt.plot(predict_2025['ds'], predict_2025['yhat'], label='Forecasted Price', linestyle='dashed')

# Add labels, title, and legend
plt.title('Comparison of Actual and Forecasted Close Prices (2024-2025)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Close Price', fontsize=12)
plt.legend()
plt.grid()

# Show the plot
plt.show()

"""When comparing the forecast and actual close prices from 2024 to 2025, the forecast matched most of the actual, as shown in the dashed line for 2024.For January to February 2025, both forecast and actual trend upward before going opposite directions."""

