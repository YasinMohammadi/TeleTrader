# domain\ports.py

from abc import ABC, abstractmethod
from .models import Signal, Order, OrderResult

class SignalParserPort(ABC):
    @abstractmethod
    def parse(self, message: str) -> Signal | None: ...

class TradingEnginePort(ABC):
    @abstractmethod
    def execute_order(self, order: Order) -> OrderResult: ...
