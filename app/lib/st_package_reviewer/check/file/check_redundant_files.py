import logging

from . import FileChecker

l = logging.getLogger(__name__)


class CheckPackageMetadata(FileChecker):

    def check(self):
        if self.sub_path("package-metadata.json").is_file():
            self.fail("'package-metadata.json' is supposed to be automatically generated "
                      "by Package Control during installation")


class CheckPycFiles(FileChecker):

    def check(self):
        pyc_files = self.glob("**/*.pyc")
        if not pyc_files:
            return

        for path in pyc_files:
            if path.with_suffix(".py").is_file():
                with self.file_context(path):
                    self.fail("'.pyc' file is redundant because its corresponding .py file exists")


class CheckCacheFiles(FileChecker):

    def check(self):
        cache_files = self.glob("**/*.cache")
        if not cache_files:
            return

        for path in cache_files:
            with self.file_context(path):
                self.fail("'.cache' file is redundant and created by ST automatically")


class CheckSublimePackageFiles(FileChecker):

    def check(self):
        cache_files = self.glob("**/*.sublime-package")
        if not cache_files:
            return

        for path in cache_files:
            with self.file_context(path):
                self.fail("'.sublime-package' files have no business being inside a package")


class CheckSublimeWorkspaceFiles(FileChecker):

    def check(self):
        cache_files = self.glob("**/*.sublime-workspace")
        if not cache_files:
            return

        for path in cache_files:
            with self.file_context(path):
                self.fail("'.sublime-workspace' files contain session data and should never be "
                          "submitted to version control")
