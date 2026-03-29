import sys
import json
import time
import websocket
import yfinance as yf
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

# --- CONFIGURACIÓN MAESTRA DE ACTIVOS ---
# Si quieres añadir más, solo añádelos a esta lista.
# fuente: "yahoo" o "binance"
ACTIVOS_CONFIG = [
    {"nombre": "S&P 500", "ticker": "^GSPC", "fuente": "yahoo"},
    {"nombre": "NASDAQ 100", "ticker": "^NDX", "fuente": "yahoo"},
    {"nombre": "DOW JONES", "ticker": "^DJI", "fuente": "yahoo"},
    {"nombre": "Russell 2000", "ticker": "^RUT", "fuente": "yahoo"},
    {"nombre": "DAX 40", "ticker": "^GDAXI", "fuente": "yahoo"},
    {"nombre": "Euro Stoxx 50", "ticker": "^STOXX50E", "fuente": "yahoo"},
    {"nombre": "IBEX 35", "ticker": "^IBEX", "fuente": "yahoo"},
    {"nombre": "Oro (Futuros)", "ticker": "GC=F", "fuente": "yahoo"},
    {"nombre": "Petróleo WTI", "ticker": "CL=F", "fuente": "yahoo"},
    {"nombre": "Mercados Emergentes", "ticker": "EEM", "fuente": "yahoo"},
    {"nombre": "EUR/USD", "ticker": "EURUSD=X", "fuente": "yahoo"},
    {"nombre": "BTC/USDT", "ticker": "btcusdt@ticker", "fuente": "binance"},
    {"nombre": "Volatilidad VIX", "ticker": "^VIX", "fuente": "yahoo"},
    {"nombre": "Vanguard S&P 500 (VUAA)", "ticker": "VUAA.DE", "fuente": "yahoo"},
    {"nombre": "Vanguard All-World (VWCE)", "ticker": "VWCE.DE", "fuente": "yahoo"}

]

# --- HILO 1: BINANCE ---
class BinanceThread(QThread):
    datos_recibidos = pyqtSignal(int, float, float, float)

    def __init__(self, fila_btc):
        super().__init__()
        self.fila_btc = fila_btc

    def run(self):
        url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
        ws = websocket.WebSocket()
        try:
            ws.connect(url)
            while True:
                mensaje = ws.recv()
                datos = json.loads(mensaje)
                precio_actual = float(datos['c'])
                var_absoluta = float(datos['p'])
                var_porcentual = float(datos['P'])
                self.datos_recibidos.emit(self.fila_btc, precio_actual, var_absoluta, var_porcentual)
        except Exception as e:
            print(f"Error en Binance: {e}")

# --- HILO 2: YAHOO FINANCE ---
class YFinanceThread(QThread):
    datos_recibidos = pyqtSignal(int, float, float, float)

    def __init__(self, diccionario_tickers):
        super().__init__()
        self.diccionario_tickers = diccionario_tickers # Formato: {'^GSPC': 0, 'GC=F': 7, ...}

    def run(self):
        while True:
            for ticker_str, fila in self.diccionario_tickers.items():
                try:
                    ticker = yf.Ticker(ticker_str)
                    precio_actual = ticker.fast_info['lastPrice']
                    precio_apertura = ticker.fast_info['previousClose']
                    
                    # Evitar división por cero si falta el dato de apertura
                    if precio_apertura and precio_apertura > 0:
                        var_abs = precio_actual - precio_apertura
                        var_porc = (var_abs / precio_apertura) * 100
                    else:
                        var_abs, var_porc = 0.0, 0.0
                        
                    self.datos_recibidos.emit(fila, precio_actual, var_abs, var_porc)
                except Exception as e:
                    pass # Silenciamos errores de red temporales
            
            # Pausa de 5 segundos para no saturar a Yahoo
            time.sleep(5)

# --- LA VENTANA PRINCIPAL ---
class ConsolaTrading(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal de Mercados Globales")
        self.resize(750, 600) # Ventana más grande para que quepan todos
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.tabla = QTableWidget(len(ACTIVOS_CONFIG), 4)
        self.tabla.setHorizontalHeaderLabels(["Activo", "Último Precio", "Variación", "% Var"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #121212; gridline-color: #333333; font-size: 14px; }
            QHeaderView::section { background-color: #2d2d2d; font-weight: bold; border: 1px solid #333333; }
        """)

        # Variables para saber qué fila le toca a cada activo
        self.fila_btc = 0
        self.tickers_yahoo = {}

        # Construir la tabla dinámicamente según la configuración maestra
        for i, config in enumerate(ACTIVOS_CONFIG):
            item_simbolo = QTableWidgetItem(config["nombre"])
            item_simbolo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 0, item_simbolo)
            
            for col in range(1, 4):
                item = QTableWidgetItem("Cargando...")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(i, col, item)

            # Clasificar si va al hilo de Binance o al de Yahoo
            if config["fuente"] == "binance":
                self.fila_btc = i
            elif config["fuente"] == "yahoo":
                self.tickers_yahoo[config["ticker"]] = i

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        widget_central = QWidget()
        widget_central.setLayout(layout)
        self.setCentralWidget(widget_central)

        # 1. Arrancar el hilo de Binance (BTC) pasándole su fila correspondiente
        self.hilo_binance = BinanceThread(self.fila_btc)
        self.hilo_binance.datos_recibidos.connect(self.actualizar_celdas)
        self.hilo_binance.start()

        # 2. Arrancar el hilo de Yahoo Finance pasándole el diccionario de los demás
        self.hilo_yfinance = YFinanceThread(self.tickers_yahoo)
        self.hilo_yfinance.datos_recibidos.connect(self.actualizar_celdas)
        self.hilo_yfinance.start()

    def actualizar_celdas(self, fila, precio, variacion_absoluta, variacion_porcentual):
        # Según el valor de mercado, mostramos más o menos decimales
        if precio > 1000:
            texto_precio = f"{precio:,.2f}"
            texto_var = f"{variacion_absoluta:+,.2f}"
        else:
            texto_precio = f"{precio:.4f}"
            texto_var = f"{variacion_absoluta:+.4f}"

        self.tabla.item(fila, 1).setText(texto_precio)
        self.tabla.item(fila, 2).setText(texto_var)
        self.tabla.item(fila, 3).setText(f"{variacion_porcentual:+.2f}%")
        
        # Colores visuales
        color_fondo = QColor("#1e3d23") if variacion_absoluta >= 0 else QColor("#4a1c1c")
        color_texto = QColor("#4caf50") if variacion_absoluta >= 0 else QColor("#f44336")
        for col in range(1, 4):
            self.tabla.item(fila, col).setBackground(color_fondo)
            self.tabla.item(fila, col).setForeground(color_texto)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ConsolaTrading()
    ventana.show()
    sys.exit(app.exec())