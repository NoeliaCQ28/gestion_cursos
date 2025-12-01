import pingouin
import pkgutil
import inspect

def find_omega(package):
    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            module = __import__(modname, fromlist="dummy")
            if hasattr(module, 'omega'):
                print(f"Found omega in {modname}")
                return
        except Exception as e:
            pass # Ignore import errors

find_omega(pingouin)
print("Search complete.")
