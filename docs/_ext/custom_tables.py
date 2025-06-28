from docutils.parsers.rst.directives.tables import RSTTable
from docutils.statemachine import StringList
from tabulate import tabulate


class ZangarDefaultMessageTable(RSTTable):
    def run(self):
        from zangar._messages import _DEFAULT_MESSAGES

        table = tabulate(
            sorted(((key, f'"{msg}"') for key, msg in _DEFAULT_MESSAGES.items())),
            headers=["Key", "Message"],
            tablefmt="rst",
        )

        self.content = StringList(table.split("\n"))
        return super().run()


def setup(app):
    app.add_directive("default-messages-table", ZangarDefaultMessageTable)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
