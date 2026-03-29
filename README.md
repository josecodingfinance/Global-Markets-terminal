📈 Global Markets Trading Console

A real-time, asynchronous desktop trading terminal built with Python and PyQt6. This application provides a unified dashboard to monitor global financial markets, including traditional indices, commodities, ETFs, and cryptocurrencies, seamlessly blending WebSocket streams with REST API polling.

✨ Features
Real-Time Crypto Data: Live, tick-by-tick updates for BTC/USDT using Binance WebSockets.
Global Market Tracking: Automated polling for major indices (S&P 500, DAX 40, IBEX 35), commodities (Gold, WTI Crude), and ETFs (VUAA, VWCE) via Yahoo Finance.
Asynchronous Architecture: Utilizes Python's QThread to separate UI rendering from data fetching, ensuring a completely freeze-free desktop experience.
Dynamic UI Styling: Professional dark-mode interface with conditional color formatting (green/red) based on absolute and percentage price variations.
Scalable Configuration: Easy-to-update dictionary structure allowing the addition of new assets with a single line of code.
🛠️ Tech Stack
Language: Python 3
GUI Framework: PyQt6
Data Providers: yfinance (Yahoo Finance API), websocket-client (Binance API)
Packaging: PyInstaller (for standalone executable generation)
🚀 Installation and Setup

If you want to run the source code directly, follow these steps:

1. Clone the repository
git clone https://github.com/yourusername/trading-console.git
cd trading-console
2. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
3. Install dependencies
pip install PyQt6 yfinance websocket-client
4. Run the application
python consola.py
📦 Building the Executable

To compile the application into a standalone executable (no Python installation required on the host machine):

pip install pyinstaller
pyinstaller --noconsole --onefile consola.py

The compiled executable will be located in the dist folder.

⚠️ Note: The executable is generated for the OS it was built on (e.g., building on Linux creates a Linux binary).

📝 Disclaimer

This software is for educational and informational purposes only. It does not constitute financial advice. Data may be subject to slight delays depending on the provider's free tier limits.
