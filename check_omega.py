try:
    from pingouin.reliability import omega
    print("Imported omega from pingouin.reliability")
except ImportError as e:
    print(f"Could not import omega: {e}")

import pingouin as pg
if hasattr(pg, 'reliability'):
    print(f"pg.reliability exists. dir: {dir(pg.reliability)}")
else:
    print("pg.reliability does not exist")
