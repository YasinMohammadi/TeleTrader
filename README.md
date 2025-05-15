
# TeleTrader 

A **Telegram/MetaTrader 5 trading bot** that turns human-readable “signal-channel” messages into fully managed MT5 orders with comprehensive risk management.
```yaml
⚜️ XAUUSD - BUY NOW
🛒 Entry : 3213
🎯 Targets :
3216
3220
3225
3230
🔺 Stoploss : 3200
💰 @Jasin Trader:Nemat 💰
```


The bot:

1.  **Parses** messages via `BasicSignalParser`.
    
2.  **Validates** and extracts multi-target `Signal` objects.
    
3.  **Generates** individual `Order`s via `OrderGenerator`.
    
4.  **Manages risk** using the `RiskManager` abstraction (default in `risk.py`).
    
5.  **Executes** orders through MT5 with `MetaTraderEngine`.
    
6.  **Replies** in Telegram with per-order statuses.

```
BUY 0.01 XAUUSD -> TP 3220.0 : OK
BUY 0.01 XAUUSD -> TP 3225.0 : OK
BUY 0.01 XAUUSD -> TP 3230.0 : OK
```

## Features

| Layer              | Package                                        | Highlights                                                                                                                      |
| ------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Domain**         | `tradebot.domain`                              | Immutable dataclasses (`Signal`, `Order`, `Target`) and port interfaces (`SignalParserPort`, `OrderGeneratorPort`, `RiskManagerPort`, `TradingEnginePort`). |
| **Application**    | `tradebot.application`                         | `BasicSignalParser`, `OrderGenerator`, and `RiskManager` implementations. No external dependencies.                                           |
| **Infrastructure** | `tradebot.infrastructure`                      | `MetaTraderEngine` (MT5), `TelegramSignalListener` (python-telegram-bot v20).                                                   |
| **Entry-point**    | `main.py`                                      | Wires everything together and starts polling.                                                                                   |
| **Tests**          | `pytest` suite for parser and order-generator. |                                                                                                                                 |
| **Logging**        | `loguru` with rotation to `tradebot.log`.      |                                                                                                                                 |
| **Config**         | `pydantic v2` settings loaded from `.env`.     |                                                                                                                                 |

## Risk Management

Risk management is abstracted via the **RiskManagerPort**. The default strategy (`application/risk.py`) uses a fixed percentage (`RISK_PER_TRADE`) of equity:

-   `RISK_PER_TRADE=0.01` means 1% of account balance per signal.
    
-   The risk manager computes **total volume**, which is then evenly split across targets.
    
-   **Swap** in a custom risk manager (e.g., ATR-based, volatility-based) by implementing `RiskManagerPort` and configuring DI in `main.py`.
- 
## Quick start

### 1. Clone & install

```bash
git clone https://github.com/YasinMohammadi/TeleTraderr.git
cd TeleTraderr
conda env create -f environment.yml (not implemented)    
conda activate Jasin-trader 

```
### 2. .env configuration

Create a `.env` file in the project root:

```ini
# Telegram
TELEGRAM_TOKEN=123456:ABC...
SIGNAL_CHAT_ID=-1001234567890      # channel/group ID you read signals from

# MT5
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT_ACCOUNT=12345678
MT_PASSWORD=demoPass
MT_SERVER=MetaQuotes-Demo

# Risk / trade settings
RISK_PER_TRADE=0.01
MAX_SLIPPAGE=20
MAGIC_NUMBER=32001

```

### 3. Launch

```bash
python -m main

```

Keep the MT5 terminal **open and logged-in**.  
Post a formatted signal into your channel – the bot will fill orders in seconds.

----------

## Signal format

-   **First line** → `SYMBOL – SIDE (LIMIT|NOW|MARKET)`  
    _`BUY NOW` is treated as a market order._
    
-   **Entry** → single price or range (`3210-3215`, lower bound used).
    
-   **Targets** under a “Targets” header, one price per line.
    
-   Optional **Stoploss** line.
    
-   Last line may contain an **@ comment**; bot extracts it and appends `Tn/N` per target.
    

### Example

```yaml
EURUSD - SELL LIMIT
Entry : 1.1000
Targets :
1.0985
1.0970
Stoploss : 1.1020
@Alice

```

## Running tests

```bash
pytest -q
```

## Extending

-   **Indicator logic** – replace `risk.py` with ATR/volatility sizing.
    
-   **Parser** – implement `AdvancedSignalParser` and swap via DI.
    
-   **Broker engines** – add `TradingEnginePort` implementations for cTrader, Binance, etc.
    
-   **Monitoring** – plug a watchdog that pings health to a dashboard.
    

