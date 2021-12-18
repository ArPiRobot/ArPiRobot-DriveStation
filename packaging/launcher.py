import importlib.util
import os

launcher_dir = os.path.realpath(os.path.dirname(__file__))

spec = importlib.util.spec_from_file_location("main", os.path.join(launcher_dir, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
