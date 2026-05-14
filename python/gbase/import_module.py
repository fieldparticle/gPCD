import importlib.util
from pathlib import Path
def load_class_from_file(file_path):
    file_path = Path(file_path).resolve()
    class_name = file_path.stem   # filename without .py

    spec = importlib.util.spec_from_file_location(class_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load: {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cls = getattr(module, class_name, None)

    if cls is None:
        raise AttributeError(
            f"File loaded, but no class named '{class_name}' exists in {file_path.name}"
        )

    return cls