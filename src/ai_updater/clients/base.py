from abc import ABC, abstractmethod
import os


class Client(ABC):
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def run(
        self, sdk_root: str, *, debug: bool, noai: bool, patch: bool, test: bool
    ): ...

    def get_sdk(self, sdk_root: str) -> str:
        filenames = next(os.walk(sdk_root), (None, None, []))[2]
        if "pyproject.toml" in filenames:
            return "python"
        if "pubspec.yaml" in filenames:
            return "flutter"
        if "package.json" in filenames:
            return "typescript"
        if "CMakeLists.txt" in filenames:
            return "cpp"
        raise ValueError(f"Unsupported SDK at {sdk_root}")
