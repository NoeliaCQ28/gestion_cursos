import sys
try:
    import pingouin as pg
    print(f"Pingouin version: {pg.__version__}")
    print(f"Has cronbach_alpha: {'cronbach_alpha' in dir(pg)}")
    print(f"Has omega: {'omega' in dir(pg)}")
except ImportError as e:
    print(f"Pingouin import error: {e}")

try:
    import sklearn
    print("sklearn installed")
except ImportError:
    print("sklearn MISSING")

try:
    import statsmodels
    print("statsmodels installed")
except ImportError:
    print("statsmodels MISSING")
