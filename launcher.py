"""
This script is simply used to load the actual program. This allows using pyinstaller, cx_Freeze, or
other similar tools to make this script into a platform specific binary. This method allows updating
the real application's python code without needing to rebuild the platform specific binary. This is
useful because there is no way to cross build for other platforms using the tools mentioned before,
nor is there an easy way to embed a python interpeter in an application package.
"""

if __name__ == "__main__":
    from app import main
