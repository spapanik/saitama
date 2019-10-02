import toml

from .common import Connection
from .migrate import Migrations
from .queries import state as state_queries


class SaveState(Connection):
    __slots__ = [
        "_settings",
        "_cli_args",
        "_prepend",
        "cursor",
        "db_options",
        "state_options",
    ]

    def __init__(self, cli_args, prepend="state", **kwargs):
        super().__init__(cli_args, prepend, **kwargs)
        self.state_options = self._state_args()

    def run(self):
        Migrations(self._cli_args, prepend=self._prepend, testing=True).run()
        self._prepare_dir()
        self._run_commands(self._write_state)

    def _state_args(self):
        return {"state_dir": self._settings.state}

    def _prepare_dir(self):
        schema = self.state_options["state_dir"].joinpath("public")
        schema.mkdir(parents=True, exist_ok=True)

    def _write_state(self):
        schema = self.state_options["state_dir"].joinpath("public")
        info = {
            "extensions": self._extensions(),
        }
        for name, output in info.items():
            path = schema.joinpath(name).with_suffix(".toml")
            if output:
                with open(path, "w") as file:
                    toml.dump(output, file)
            else:
                del path

    def _create_info_dict(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        columns = [column.name for column in self.cursor.description]
        return {row[0]: dict(zip(columns, row)) for row in result}

    def _extensions(self):
        return self._create_info_dict(state_queries.extensions)
