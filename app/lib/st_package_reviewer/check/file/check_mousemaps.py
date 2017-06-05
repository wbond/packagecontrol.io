from pathlib import Path

from . import FileChecker


DATA_PATH = Path(__file__).parent.parent / "data"

PLATFORMS = ("Linux", "OSX", "Windows")
PLATFORM_FILENAMES = tuple("Default ({}).sublime-mousemap".format(plat)
                           for plat in PLATFORMS)
VALID_FILENAMES = PLATFORM_FILENAMES + ("Default.sublime-mousemap",)


class CheckMousemaps(FileChecker):

    def check(self):
        mousemap_files = self.glob("**/*.sublime-mousemap")

        # ignore unused files
        mousemap_files = {path for path in mousemap_files
                          if path.name in VALID_FILENAMES}

        if not mousemap_files:
            return

        # just warn about mousemap files existing
        for path in mousemap_files:
            with self.file_context(path):
                self.warn("It is not advised to specify mousemaps because of how limited the "
                          "configuration options are. Instead, suggest the user to add "
                          "specific bindings to their User package.")
