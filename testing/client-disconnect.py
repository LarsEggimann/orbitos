from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui
from starlette.middleware.base import BaseHTTPMiddleware
from static.global_ui_props import *

# in users passwords would obviously need to be hashed
passwords = {"lars": "topsecret"}

unrestricted_page_routes = {"/login"}


class AuthMiddleware(BaseHTTPMiddleware):
    """This middleware restricts access to all NiceGUI pages.
    It redirects the user to the login page if they are not authenticated.
    """

    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get("authenticated", False):
            if (
                request.url.path in Client.page_routes.values()
                and request.url.path not in unrestricted_page_routes
            ):
                app.storage.user["referrer_path"] = (
                    request.url.path
                )  # remember where the user wanted to go
                return RedirectResponse("/login")
        return await call_next(request)


def logout_buttons() -> None:
    with ui.column():

        ui.label(f'Hello {app.storage.user["username"]}!').classes("text-2xl")

        ui.button(
            text="Log out",
            on_click=lambda: (
                app.storage.user.update({"authenticated": False}),
                ui.navigate.to("/login"),
            ),
            icon="logout",
        ).props(props_button)


@ui.page("/login")
def login() -> Optional[RedirectResponse]:
    ui.colors(primary=app.storage.user.get("primary-color", "#69501b"))
    ui_dark_mode = ui.dark_mode()
    ui_dark_mode.value = app.storage.user.get("dark-mode", False)

    def try_login() -> (
        None
    ):  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({"username": username.value, "authenticated": True})
            ui.navigate.to(app.storage.user.get("referrer_path", "/"))
            # ui.navigate.to("/main")
        else:
            ui.notify("Wrong username or password", color="negative")

    if app.storage.user.get("authenticated", False):
        return RedirectResponse("/main")
    with ui.card().classes("absolute-center"):
        ui.label("Log in to ORBITOS").classes("text-2xl")
        username = ui.input("Username").on("keydown.enter", try_login).classes("w-full")
        password = (
            ui.input("Password", password=True, password_toggle_button=True)
            .on("keydown.enter", try_login)
            .classes("w-full")
        )
        ui.button("Log in", on_click=try_login).props(props_button)
    return None


@ui.page("/main")
async def main():
    ui.label("main page")


if __name__ in {"__main__", "__mp_main__"}:

    app.add_middleware(AuthMiddleware)

    ui.navigate.to("/main")

    ui.run(
        reload=True,
        show=False,
        on_air=None,
        binding_refresh_interval=0.1,
        host="0.0.0.0",
        title="ORBITOS",
        port=50050,
        storage_secret="crazy-ass-secret",
    )
