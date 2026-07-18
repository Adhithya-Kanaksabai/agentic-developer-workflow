from sandbox.protocol import BaseSandbox

class MockSandbox(BaseSandbox):
    async def run_command(self, cmd: str) -> tuple[int, str, str]:
        # Mock success output for V1
        return 0, "Mock execution: Success", ""
        
    async def write_file(self, path: str, content: str) -> None:
        pass
