import os
import json
import time
import asyncio
import traceback
from decimal import Decimal, ROUND_DOWN

from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException

# --- CONFIGURACIÓN ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Lista de pares actualizada (Incluye PAXG)
PAIRS = [
    {"symbol": "BTCUSDT", "ws": "btcusdt"},
    {"symbol": "ETHUSDT", "ws": "ethusdt"},
    {"symbol": "ETHBTC",  "ws": "ethbtc"},
    {"symbol": "PAXGUSDT", "ws": "paxgusdt"}, # Agregado (Nota: PAXG va primero)
    {"symbol": "PAXGBTC",  "ws": "paxgbtc"}    # Agregado
]

# Parámetros de Estrategia
DROP_BUY = Decimal("0.001")       # Compra si baja 0.1% desde máximo reciente
TAKE_PROFIT = Decimal("0.002")    # Vende si sube 0.2% desde compra

# Archivos de estado
POSITIONS_FILE = "positions.json"
LOG_FILE = "bot_log.txt"

# Estado global
positions = {}
filters_cache = {}
peak_prices = {} 
trading_active_flags = {} 

# --- UTILIDADES ---
def log(text):
    msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {text}"
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception: pass

def save_positions():
    try:
        with open(POSITIONS_FILE, "w", encoding="utf-8") as f:
            data_to_save = {}
            for k, v in positions.items():
                data_to_save[k] = {
                    "entry": float(v["entry"]),
                    "quantity": float(v["quantity"]),
                    "sell_price": float(v["sell_price"]),
                    "sell_order_id": v["sell_order_id"]
                }
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        log(f"Error guardando posiciones JSON: {e}")

def load_positions():
    global positions
    if os.path.exists(POSITIONS_FILE):
        try:
            with open(POSITIONS_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                positions = {}
                for k, v in raw_data.items():
                    positions[k] = {
                        "entry": Decimal(str(v["entry"])),
                        "quantity": Decimal(str(v["quantity"])),
                        "sell_price": Decimal(str(v["sell_price"])),
                        "sell_order_id": v["sell_order_id"]
                    }
            log(f"Posiciones cargadas: {list(positions.keys())}")
        except Exception as e:
            log(f"Error cargando archivo de posiciones: {e}. Iniciando vacío.")
            positions = {}

def round_step(value, step):
    return value.quantize(step, rounding=ROUND_DOWN)

async def get_exchange_filters(client, symbol):
    if symbol in filters_cache:
        return filters_cache[symbol]
    try:
        info = await client.get_symbol_info(symbol)
        step_size = None
        tick_size = None

        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step_size = Decimal(f["stepSize"])
            if f["filterType"] == "PRICE_FILTER":
                tick_size = Decimal(f["tickSize"])
        
        if step_size and tick_size:
            filters_cache[symbol] = (step_size, tick_size)
            return step_size, tick_size
    except Exception as e:
        log(f"Error obteniendo filtros para {symbol}: {e}")
    return None, None

# --- GESTIÓN DE ÓRDENES ---

async def place_market_buy_and_limit_sell(client, symbol):
    """Modo ALL-IN dinámico y asíncrono"""
    try:
        step_size, tick_size = await get_exchange_filters(client, symbol)
        if not step_size or not tick_size: return

        # Determinar automáticamente la moneda puente (Quote Asset)
        if symbol.endswith("USDT"):
            quote_asset = "USDT"
            precision = Decimal("0.01")       
            min_funds = Decimal("5.1")        
        elif symbol.endswith("BTC"):
            quote_asset = "BTC"
            precision = Decimal("0.000001")   
            min_funds = Decimal("0.0001")     
        else:
            log(f"[{symbol}] Par no configurado para All-In automático.")
            trading_active_flags[symbol] = True
            return

        # Consultar el saldo libre real
        balance = await client.get_asset_balance(asset=quote_asset)
        available_balance = Decimal(balance["free"])

        if available_balance < min_funds:
            log(f"[{symbol}] Saldo {quote_asset} insuficiente para operar: {available_balance}")
            trading_active_flags[symbol] = True
            return

        qty_to_spend = round_step(available_balance, precision)

        log(f"[{symbol}] Estrategia cumplida. Lanzando orden de COMPRA ALL-IN usando {qty_to_spend} {quote_asset}")

        # Ejecutar compra de MERCADO gastando todo el saldo disponible
        buy_order = await client.order_market_buy(
            symbol=symbol,
            quoteOrderQty=float(qty_to_spend)
        )

        executed_qty = Decimal(buy_order["executedQty"])
        spent_quote = Decimal(buy_order["cummulativeQuoteQty"])
        avg_entry = spent_quote / executed_qty

        log(f"[{symbol}] COMPRA EJECUTADA. Comprado: {executed_qty}, Entrada Media: {avg_entry:.6f}")

        # Calcular Precio de Venta objetivo
        raw_sell_price = avg_entry * (Decimal("1") + TAKE_PROFIT)
        sell_price = round_step(raw_sell_price, tick_size)

        # Calcular Cantidad a vender
        qty_to_sell = round_step(executed_qty, step_size)

        log(f"[{symbol}] Colocando orden LIMIT VENTA: {qty_to_sell} a {sell_price:.6f}")

        # Colocar orden LIMIT de VENTA
        sell_order = await client.order_limit_sell(
            symbol=symbol,
            quantity=float(qty_to_sell),
            price=str(sell_price)
        )

        # Registrar posición de forma segura
        positions[symbol] = {
            "entry": avg_entry,
            "quantity": qty_to_sell,
            "sell_price": sell_price,
            "sell_order_id": sell_order["orderId"]
        }
        trading_active_flags[symbol] = False 
        save_positions()
        
    except BinanceAPIException as e:
        log(f"[{symbol}] ERROR BINANCE EN COMPRA/VENTA: {e.message}")
        if symbol not in positions: trading_active_flags[symbol] = True
    except Exception as e:
        log(f"[{symbol}] ERROR GENERAL EN EJECUCIÓN: {e}")
        traceback.print_exc()
        if symbol not in positions: trading_active_flags[symbol] = True

# --- TAREAS DE MONITOREO ---

async def user_data_stream_task(client):
    bsm = BinanceSocketManager(client)
    async with bsm.user_socket() as stream:
        log("CONECTADO A USER DATA STREAM (Monitoreando tus ventas)")
        while True:
            try:
                msg = await stream.recv()
                
                if msg.get("e") == "executionReport":
                    symbol = msg.get("s")
                    order_status = msg.get("X")
                    order_id = msg.get("i")
                    side = msg.get("S")
                    
                    if symbol in positions and side == "SELL" and order_status == "FILLED":
                        if order_id == positions[symbol]["sell_order_id"]:
                            log(f"[{symbol}] ✅ VENTA LIMIT EJECUTADA EN BINANCE.")
                            
                            del positions[symbol]
                            save_positions()
                            
                            if symbol in peak_prices: del peak_prices[symbol]
                            
                            trading_active_flags[symbol] = True
                            log(f"[{symbol}] Capital liberado. Reiniciando rastreo desde precio actual.")

            except asyncio.CancelledError: break
            except Exception as e:
                log(f"Error en User Data Stream loop: {e}")
                await asyncio.sleep(5)

async def price_monitor_task(client):
    streams = [f"{p['ws']}@aggTrade" for p in PAIRS]
    bsm = BinanceSocketManager(client)
    
    async with bsm.multiplex_socket(streams) as stream:
        log(f"CONECTADO A PRECIOS DE MERCADO: {streams}")
        while True:
            try:
                msg = await stream.recv()
                if not msg or 'data' not in msg: continue
                
                data = msg['data']
                symbol = data['s']
                price = Decimal(str(data['p']))

                if symbol in positions or not trading_active_flags.get(symbol, True):
                    continue

                if symbol not in peak_prices:
                    peak_prices[symbol] = price
                    continue

                if price > peak_prices[symbol]:
                    peak_prices[symbol] = price
                    continue

                current_peak = peak_prices[symbol]
                if current_peak == 0: continue 
                
                drop = (current_peak - price) / current_peak

                if drop >= DROP_BUY:
                    log(f"[{symbol}] Estrategia activa: Caída de {drop*100:.2f}% (Precio: {price}, Máx: {current_peak})")
                    trading_active_flags[symbol] = False
                    asyncio.create_task(place_market_buy_and_limit_sell(client, symbol))

            except asyncio.CancelledError: break
            except Exception as e:
                log(f"Error en Price Monitor loop: {e}")
                await asyncio.sleep(2)

async def main():
    if not API_KEY or not API_SECRET:
        print("Error: Configura BINANCE_API_KEY y BINANCE_API_SECRET en tu entorno.")
        return

    log("=== INICIANDO BOT ALL-IN ASÍNCRONO ===")
    load_positions()
    
    for pair in PAIRS:
        sym = pair["symbol"]
        trading_active_flags[sym] = (sym not in positions)

    client = await AsyncClient.create(API_KEY, API_SECRET)

    try:
        for pair in PAIRS:
            await get_exchange_filters(client, pair["symbol"])

        await asyncio.gather(
            user_data_stream_task(client),
            price_monitor_task(client)
        )
    except KeyboardInterrupt:
        log("Bot detenido manualmente.")
    except Exception as e:
        log(f"ERROR FATAL: {e}")
        traceback.print_exc()
    finally:
        log("Cerrando conexión...")
        await client.close_connection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass