from . import AstChecker


class CheckOsSystemCalls(AstChecker):
    """Checks for any calls to os.system and suggests to use subprocess.check_call instead."""

    def _warn_about_os_system(self, node):
        self.warn("Consider replacing os.system with subprocess.check_output,"
                  " or use sublime's Default.exec.ExecCommand. "
                  "Also make sure you thought about the platform key in your pull request.")

    def visit_Call(self, node):
        try:
            attr = node.func.attr
            id = node.func.value.id
        except Exception as e:
            return
        if id == "os" and attr == "system":
            self._warn_about_os_system(node)
