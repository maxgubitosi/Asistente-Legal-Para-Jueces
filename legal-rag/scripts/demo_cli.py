import typer, rich
from app.rag import answer

cli = typer.Typer()

@cli.command()
def ask(q: list[str] = typer.Argument(..., help="Pregunta")):
    """
    Ejemplo:
        python -m scripts.demo_cli ask Listame fallos donde se discuta la constitución en mora
    o, con comillas:
        python -m scripts.demo_cli ask "Listame fallos …"
    """
    query = " ".join(q)          # une todos los tokens en una sola frase
    markdown, _ = answer(query)
    rich.print(markdown)

if __name__ == "__main__":
    cli()
