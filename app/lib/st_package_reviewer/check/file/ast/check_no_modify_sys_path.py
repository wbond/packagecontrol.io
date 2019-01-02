from . import AstChecker


class CheckNoModifySysPath(AstChecker):
    """Checks for modifications to sys.path."""

    def _warn_about_modify_sys_path(self, node):
        with self.node_context(node):
            self.warn("Modifying sys.path is usually a bad idea and can interfere with other"
                      " packages. Consider using relative imports instead.")

    def visit_Call(self, node):
        try:
            func = node.func

            if (
                func.attr in {'append', 'insert'}
                and func.value.attr == 'path'
                and func.value.value.id == 'sys'
            ):
                self._warn_about_modify_sys_path(node)
        except Exception as e:
            return
