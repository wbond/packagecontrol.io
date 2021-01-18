import re

from . import FileChecker


class CheckLicense(FileChecker):

    def check(self):
        has_license = any(
            True for p in self.base_path.iterdir()
            if re.search(r'(?i)^(un)?license', p.name)
        )

        if not has_license:
            self.warn("The package does not contain a top-level LICENSE file."
                      " A license helps users to contribute to the package.")
