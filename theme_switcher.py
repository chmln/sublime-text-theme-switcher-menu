import sublime
import sublime_plugin
import os


def menu_cache_path():
    """
    Return absolute path for plugin's main menu cache dir.
    """
    return sublime.packages_path() + "/User/Theme-Switcher.cache/"


def built_res_name(pkg_name):
    """
    Built a beautiful menu or quick panel item name from a resource file name
    """
    return os.path.basename(pkg_name[:pkg_name.rfind(".")]).replace("-", " ").replace(".", " ")


def plugin_loaded():
    """
    API entry point
    Refresh cached Main.sublime-menu if plugin is loaded.
    """
    RefreshThemeCacheCommand().run()


def plugin_unloaded():
    """
    API entry point
    Clear cached Main.sublime-menu if the plugin is disabled or removed.
    """
    try:
        from shutil import rmtree
        rmtree(menu_cache_path())
    except:
        pass


class RefreshThemeCacheCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        """
        API entry point
        rebuild main menu
        """

        # create cache directory
        cache_path = menu_cache_path()
        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)

        # build main menu structure
        menu = [{
            "id": "preferences",
            "children": [{
                "caption": "Theme",
                "id": "theme",
                "children" : self.create_menu("switch_theme",
                                              "*.sublime-theme")
            }]
        }]

        # save main menu to file
        with open(cache_path + "Main.sublime-menu", "w") as f:
            f.write(sublime.encode_value(menu, False))


    @staticmethod
    def create_menu(command, file_pattern):
        d = {}

        for path in sublime.find_resources(file_pattern):
            elems = path.split("/")
            # elems[1] package name
            # elems[-1] theme file name
            d.setdefault(elems[1], []).append(elems[-1])

        menu = [{
            "caption": package_name,
            "children": [{
                "caption": built_res_name(theme),
                "command": command,
                "args": { "name": theme }
                } for theme in sorted(themes, key = lambda x:x.replace(".", " ")) ]
            } for package_name, themes in sorted(d.items()) ]

        menu.append({"caption": "-", "id": "separator"});
        menu.append({"caption": "Refresh Theme Cache", "command": "refresh_theme_cache"})

        return menu


class SwitchWindowCommandBase(sublime_plugin.WindowCommand):
    """
    This is a base class for a window command to apply changes to
    the Preferences.sublime-settings.

    It is used to switch between all available themes and color schemes
    with the help of the quick panel.
    """

    def __init__(self, window):
        self.window = window
        self.settings = sublime.load_settings("Preferences.sublime-settings")

    def run(self, name = None):
        """
        API entry point for command execution for both
        SwitchThemeCommand and SwitchColorSchemeCommand
        """

        if name:
            # A theme or color scheme file name is provided,
            # so persistently apply it, if valid.
            if any(sublime.find_resources(os.path.basename(name))):
                self.settings.set(self.KEY, name)
                sublime.save_settings("Preferences.sublime-settings")

            else:
                sublime.status_message(name + " does not exist!")

        else:
            # No theme or color scheme file name is provided,
            # so let the user choose from the list of existing ones.
            names, values = self.get_items()
            current_value = self.settings.get(self.KEY)

            try:
                selected_index = values.index(current_value)
            except ValueError:
                selected_index = -1

            self.window.show_quick_panel(
                items = names,
                selected_index = selected_index,
                on_highlight = lambda x: self.settings.set(self.KEY, values[x]),
                on_select = lambda x: self.on_select(values[x], x < 0, current_value))

    def on_select(self, value, abort, abort_value):
        if abort:
            value = abort_value

        self.settings.set(self.KEY, value)
        sublime.save_settings("Preferences.sublime-settings")


class SwitchThemeCommand(SwitchWindowCommandBase):
    KEY = 'theme'

    @staticmethod
    def get_items():
        """
        Return a list of all themes to show in the quick panel.
        The values are the basename of each *.sublime-theme.
        """
        names = []
        values = []
        for path in sorted(sublime.find_resources("*.sublime-theme"), key = lambda x:os.path.basename(x)):
            elems = path.split("/")
            names.append([ built_res_name(elems[-1]),    # title
                           "Package: " + elems[1] ])     # description
            values.append(elems[-1])

        return [names, values]


class SwitchColorSchemeCommand(SwitchWindowCommandBase):
    KEY = 'color_scheme'

    @staticmethod
    def get_items():
        """
        Return a list of all color schemes to show in the quick panel.
        The values are the full path of each *.tmTheme.
        """
        names = []
        values = []
        for path in sorted(sublime.find_resources("*.tmTheme"), key = lambda x:os.path.basename(x)):
            elems = path.split("/")
            names.append([ built_res_name(elems[-1]),    # title
                           "Package: " + elems[1] ])     # description
            values.append(path)

        return [names, values]
