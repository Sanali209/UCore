# examples/web_flet/main.py
import sys
import time
import flet as ft

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.ui.flet_adapter import FletAdapter
from framework.config import Config

# This is the main function for the Flet UI
def flet_main(page: ft.Page):
    """
    This function defines the Flet UI. It's passed to the FletAdapter.
    """
    page.title = "UCore Flet Example"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)

    def minus_click(e):
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()

    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)
        page.update()

    page.add(
        ft.Row(
            [
                ft.IconButton(icon="remove", on_click=minus_click),
                txt_number,
                ft.IconButton(icon="add", on_click=plus_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

def create_flet_app():
    """
    Application factory for the Flet app.
    """
    # 1. Initialize the main App object
    app = App(name="UCoreFletExample")

    # 2. Register the FletAdapter.
    # We pass the flet_main function as the target for the Flet app.
    flet_adapter = FletAdapter(app, target_func=flet_main)
    app.register_component(lambda: flet_adapter)

    # You could register other non-UI components here as well.
    # For example, an HTTP client, a database service, etc.
    # These services could then be accessed from within the Flet UI
    # through a shared context or by using the DI container if Flet's
    # architecture allows for it (which is more advanced).

    return app

if __name__ == "__main__":
    # Create the application instance
    ucore_app = create_flet_app()
    
    # Run the application. This will start the main asyncio event loop.
    # The FletAdapter's start() method will be called, launching the
    # Flet web server in a separate thread.
    ucore_app.run()
