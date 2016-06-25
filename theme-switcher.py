import sublime
import sublime_plugin
import os


def create_menu():
    menu=[]
    d={}

    for path in sublime.find_resources("*.sublime-theme"):
        path_parts=path.split("/")
        # path_parts[1] package name
        # path_parts[-1] theme file name
        d.setdefault(path_parts[1], []).append(path_parts[-1])

    for theme_group in sorted(d.keys()):
        menu.append({
            "caption": theme_group,
            "children": [
                {
                    "caption": parse_pkg_name(theme),
                    "command": "switch_theme",
                    "args": {"name": theme}
                }
                for theme in sorted(d[theme_group], key=lambda x:x.replace(".", " "))
            ]
        })

    menu.append({"caption": "-", "id": "separator"});
    menu.append({"caption": "Refresh Theme Cache", "command": "refresh_theme_menu"})

    return menu


def parse_pkg_name(pkg_name):
    return pkg_name[:pkg_name.rfind(".")].replace("-", " ").replace(".", " ")


def plugin_loaded():
    """
        Refresh cached Main.sublime-menu if plugin is loaded.
    """
    global PKG_FOLDER, THEMES_MENU

    PKG_FOLDER=os.path.join(sublime.packages_path(), "User/Theme-Switcher.cache")
    THEMES_MENU=os.path.join(PKG_FOLDER, "Main.sublime-menu")

    if not os.path.isdir(PKG_FOLDER):
        os.makedirs(PKG_FOLDER)

    menu=sublime.decode_value("""
                    [{
                        "id": "preferences",
                        "children":
                        [{
                            "caption": "Theme",
                            "id": "themes"
                        }]
                    }]
                    """)
    menu[0]['children'][0]['children']=create_menu()
    with open(THEMES_MENU, "w") as f:
        f.write(sublime.encode_value(menu, True))


def plugin_unloaded():
    """
        Clear cached Main.sublime-menu if the plugin is disabled or removed.
    """
    global PKG_FOLDER, THEMES_MENU

    try:
        os.remove(THEMES_MENU)
    except:
        pass

    try:
        os.rmdir(PKG_FOLDER)
    except:
        pass


class RefreshThemeMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        plugin_loaded()


class SwitchCommandBase(sublime_plugin.WindowCommand):
    """
        This is a base class for a window command to apply changes to
        the Preferences.sublime-settings.

        It is used to switch between all available themes and color schemens
        with the help of the quick panel.
    """

    def run(self, name=None):
        """
            This command has two functions.
            1. If no <name> is provided, it shows a quick panel on the active
               window with all available themes or color schemes.
            2. If <name> is a valid string, the provided theme or color scheme is applied.
        """
        if name:
            self.apply(name)
        else:
            [names, values] = self.get_items()
            self.window.show_quick_panel(
                items=names,
                on_select=lambda x: self.apply(values[x]),
                flags=sublime.KEEP_OPEN_ON_FOCUS_LOST)

    def apply(self, name):
        sublime.load_settings("Preferences.sublime-settings").set(self.KEY, name)
        sublime.save_settings("Preferences.sublime-settings")


class SwitchThemeCommand(SwitchCommandBase):
    KEY = 'theme'

    def get_items(self):
        """
            Return a list of all available themes to show in the quick panel
            with the following format:
            1. title (_items[0]) to show in the list and
            2. values (_items[1]) to write to the Preferences.sublime-settings

            In this case the values are the basename of each *.sublime-theme.
        """
        names = []
        values = []
        for path in sorted(sublime.find_resources("*.sublime-theme")):
            path = os.path.basename(path)
            names.append(parse_pkg_name(path))
            values.append(path)

        return [names, values]


class SwitchColorSchemeCommand(SwitchCommandBase):
    KEY = 'color_scheme'

    def get_items(self):
        """
            Return a list of all available color schemes to show in the quick panel
            with the following format:
            1. title (_items[0]) to show in the list and
            2. values (_items[1]) to write to the Preferences.sublime-settings

            In this case the values are the full path of each *.tmTheme.
        """
        names = []
        values = []
        for path in sorted(sublime.find_resources("*.tmTheme")):
            names.append(parse_pkg_name(os.path.basename(path)))
            values.append(path)

        return [names, values]

