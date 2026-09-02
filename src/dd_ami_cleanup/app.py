import typer

from .run import app as run_app

app = typer.Typer()
app.add_typer(run_app)
