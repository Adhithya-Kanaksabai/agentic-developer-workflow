from abc import ABC, abstractmethod

class BaseSandbox(ABC):
    @abstractmethod
    async def run_command(self, cmd: str) -> tuple[int, str, str]:
        pass
        
    @abstractmethod
    async def write_file(self, path: str, content: str) -> None:
        pass
