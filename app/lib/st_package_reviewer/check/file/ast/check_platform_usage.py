from . import AstChecker


class CheckPlatformUsage(AstChecker):
    """If the plugin uses the platform package and/or sublime.platform(), issue a warning."""

    def _warn_platform_module_usage(self, node):
        with self.node_context(node):
            self.warn("It looks like you're using platform-dependent code."
                      " Make sure you thought about the platform key in your pull request."
                      " Also consider replacing the platform module with"
                      " sublime.platform() and sublime.arch().")

    def _warn_sublime_platform_usage(self, node):
        with self.node_context(node):
            self.warn("It looks like you're using platform-dependent code."
                      " Make sure you thought about the platform key in your pull request.")

    def visit_Import(self, node):
        for alias_node in node.names:
            name = alias_node.name
            if name == "platform":
                self._warn_platform_module_usage(node)

    def visit_ImportFrom(self, node):
        if node.module == "platform":
            self._warn_platform_module_usage(node)

    def visit_Call(self, node):
        try:
            attr = node.func.attr
            id_ = node.func.value.id
        except Exception as e:
            return
        if id_ == "sublime" and attr in ("platform", "arch"):
            self._warn_sublime_platform_usage(node)
