from core.app import App
from ui.screens.main_menu import MainMenuScreen


def main():
    app = App()
    app.screens.push(MainMenuScreen(app.screens))
    app.run()


if __name__ == "__main__":
    main()
