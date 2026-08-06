# Copyright (c) 2025 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.


"""local server
Run this.

Examples:
```
uv run python -m cli local_server run
```

"""

import os
import subprocess

import typer


app = typer.Typer(no_args_is_help=True, help="local trust trial")

COMMAND_NAME = "local_server"


@app.command("run")
def run(
    port: str = typer.Option("8000", "--port", "-p", help="port No."),
    env: str = typer.Option(
        os.environ.get("ENV", "LOCAL"),
        "--env",
        "-e",
        help="Runtime environment (LOCAL)",
    ),
):
    """Run local test."""
    proc_env = os.environ.copy()
    proc_env.setdefault("ENV", env)
    subprocess.run(
        ["uv", "run", "uvicorn", "trust.main:app", "--port", str(port)],
        check=True,
        env=proc_env,
    )
