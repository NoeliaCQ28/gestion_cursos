import pingouin as pg
import sys

print(f"Pingouin version: {pg.__version__}")

if hasattr(pg, 'omega'):
    print("pg.omega exists")
else:
    print("pg.omega does NOT exist")

try:
    from pingouin.reliability import omega
    print("Successfully imported omega from pingouin.reliability")
except ImportError:
    print("Could not import omega from pingouin.reliability")
except Exception as e:
    print(f"Error importing from pingouin.reliability: {e}")

try:
    import pingouin.reliability
    print(f"Contents of pingouin.reliability: {dir(pingouin.reliability)}")
except Exception as e:
    print(f"Error inspecting pingouin.reliability: {e}")
