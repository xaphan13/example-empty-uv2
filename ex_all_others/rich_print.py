from config_log import ConfigLogger

logF = ConfigLogger.get_logger("OnlyFile")

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.pretty import Pretty
from rich import print as r_print, inspect

console = Console()


def rich_console_text():
    logF.info(f"'****' rich_console_text - 'start'")

    inspect(logF, methods=False, private=False, docs=False)
    a, b, c = 1111111111111, 22222222222222, 333333333333333
    text111, text222, text333 = Text("4444444444444444"), Text("5555555555555555"), Text("5555555555555555")

    print(locals())
    r_print(locals())
    pretty = Pretty(locals())
    panel = Panel(pretty)
    r_print(panel)

    panel = Panel(
        Text("Panel(Text) : justify=right : style=red", style="red", justify="right"),
        title="Title text",
    )
    r_print(panel)

    text0 = Text("Text, text.stylize(bold magenta, 0, 6)")
    text0.stylize("bold magenta", 0, 6)
    console.print(text0)

    text1 = Text()
    text1.append("text.append = style=blue", style="blue")
    text1.append(" simple text append")
    console.print(text1)

    text2 = Text.assemble(("Text.assemble = yellow", "yellow"), " + simple text")
    console.print(text2)

    blue_console = Console(style="white on yellow")
    blue_console.print("11 222 (скобки) <угловые> {фигурные} g=7 style=white on-red")
    text3 = Text.assemble(("33 444 Text.assemble = (blue)", "blue"), " + (ff) blue_console")
    blue_console.print(text3)
