import importlib.util
import sys

dependencies = ['pingouin', 'pandas', 'numpy', 'scipy', 'sklearn', 'statsmodels']

print(f"Python version: {sys.version}")

for dep in dependencies:
    spec = importlib.util.find_spec(dep)
    if spec is None:
        print(f"{dep}: NOT FOUND")
    else:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"{dep}: {version}")
        except Exception as e:
            print(f"{dep}: Found but error importing: {e}")
