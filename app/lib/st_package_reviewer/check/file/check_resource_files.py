import logging

from . import FileChecker


l = logging.getLogger(__name__)


class CheckPluginsInRoot(FileChecker):

    def check(self):
        if self.glob("*.py"):
            return

        python_files_in_package = self.glob("*/**/*.py")
        if python_files_in_package:
            l.debug("Non-plugin Python files: %s", python_files_in_package)
            if not self.glob("**/*.sublime-build"):
                self.fail("The package contains {} Python file(s), "
                          "but none of them are in the package root "
                          "and no build system is specified"
                          .format(len(python_files_in_package)))


class CheckHasResourceFiles(FileChecker):

    def check(self):
        resource_file_globs = {
            "*.py",
            "**/*.sublime-build",
            "**/*.sublime-commands",
            "**/*.sublime-completions",
            "**/*.sublime-keymap",
            "**/*.sublime-macro",  # almost useless without other files
            "**/*.sublime-menu",
            "**/*.sublime-mousemap",
            "**/*.sublime-settings",
            "**/*.sublime-snippet",
            "**/*.sublime-syntax",
            "**/*.sublime-theme",
            "**/*.tmLanguage",
            "**/*.tmPreferences",
            "**/*.tmSnippet",
            "**/*.tmTheme",
            # hunspell dictionaries
            "**/*.aff",
            "**/*.dic",
        }

        has_resource_files = any(self.glob(ptrn) for ptrn in resource_file_globs)
        if not has_resource_files:
            self.fail("The package does not define any file that interfaces with Sublime Text")


class CheckHasSublimeSyntax(FileChecker):

    selector = None

    def set_selector(self, selector):
        self.selector = selector

    def st_build_match(self, ver):
        min_version = float("-inf")
        max_version = float("inf")

        if self.selector == '*':
            return True

        gt_match = re.match('>(\d+)$', self.selector)
        ge_match = re.match('>=(\d+)$', self.selector)
        lt_match = re.match('<(\d+)$', self.selector)
        le_match = re.match('<=(\d+)$', self.selector)
        range_match = re.match('(\d+) - (\d+)$', self.selector)

        if gt_match:
            min_version = int(gt_match.group(1)) + 1
        elif ge_match:
            min_version = int(ge_match.group(1))
        elif lt_match:
            max_version = int(lt_match.group(1)) - 1
        elif le_match:
            max_version = int(le_match.group(1))
        elif range_match:
            min_version = int(range_match.group(1))
            max_version = int(range_match.group(2))
        else:
            return None

        if min_version > ver:
            return False
        if max_version < ver:
            return False

        return True

    def check(self):
        syntax_files = self.glob("**/*.sublime-syntax")

        for path in syntax_files:
            if (
                not path.with_suffix(".tmLanguage").is_file()
                and not path.with_suffix(".hidden-tmLanguage").is_file()
            ):
                if not self.st_build_match(3091) and not self.st_build_match(2221):
                    continue
                with self.file_context(path):
                    self.warn("'.sublime-syntax' support has been added in build 3092 and there "
                              "is no '.tmLanguage' fallback file")
