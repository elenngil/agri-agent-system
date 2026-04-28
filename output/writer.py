import json
from pathlib import Path
from dataclasses import asdict, is_dataclass
from datetime import date, datetime


class OutputWriter:
    def __init__(self, output_path: str = "output/daily_plan.json"):
        self.output_path = Path(output_path)

    def _to_jsonable(self, obj):
        if obj is None:
            return None

        if isinstance(obj, (str, int, float, bool)):
            return obj

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        if isinstance(obj, set):
            return list(obj)

        if isinstance(obj, list):
            return [self._to_jsonable(x) for x in obj]

        if isinstance(obj, tuple):
            return [self._to_jsonable(x) for x in obj]

        if isinstance(obj, dict):
            return {str(k): self._to_jsonable(v) for k, v in obj.items()}

        if is_dataclass(obj):
            return self._to_jsonable(asdict(obj))

        if hasattr(obj, "__dict__"):
            return self._to_jsonable(obj.__dict__)

        return str(obj)

    def write(self, state):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        data = self._to_jsonable(state)

        with self.output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)