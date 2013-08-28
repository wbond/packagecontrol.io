# Setup Scripts

The `export.py` and `import.py` scripts are used for extracting anonymized
usage information from the Package Control website for use during development.

`extract_package_control.py` will take the necessary files from an un-packed
version of Package Control and place them in the `app/lib/package_control/`
folder. This makes it easy for the site to stay up-to-date with the package.
