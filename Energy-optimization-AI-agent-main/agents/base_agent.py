"""
Base Agent Class
All agents inherit from this class.
"""

from abc import ABC, abstractmethod
import time

from services.logger import setup_logger


class BaseAgent(ABC):
    """
    Base class for every agent.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(name)

    @abstractmethod
    def run(self, data):
        """
        Every agent must implement this method.
        """
        pass

    def execute(self, data):
        """
        Execute the agent while automatically logging execution time.
        """

        self.logger.info(f"{self.name} started.")

        start = time.perf_counter()

        result = self.run(data)

        end = time.perf_counter()

        elapsed = end - start

        self.logger.info(
            f"{self.name} completed in {elapsed:.3f} seconds."
        )

        return result