# strategy.py
from abc import ABC, abstractmethod

class ScraperStrategy(ABC):
    @abstractmethod
    def scrape(self, url):
        pass
