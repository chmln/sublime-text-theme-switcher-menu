import sublime
import sublime_plugin
import os


def menu_cache_path():
    """Return absolute path for plugin's main menu cache dir."""
    return sublime.packages_path() + "/User/Theme-Switcher.cache/"


def built_res_name(pkg_name):
    """Built menu or quick panel item name from a resource file name."""
    name, _ = os.path.splitext(os.path.basename(pkg_name))
    return name.replace("-", " ").replace(".", " ")


def plugin_loaded():
    """Refresh cached Main.sublime-menu after plugin is loaded."""
    RefreshThemeCacheCommand().run()


def plugin_unloaded():
    """Clear cached Main.sublime-menu if the plugin is unloaded."""
    try:
        from shutil import rmtree
        rmtree(menu_cache_path())
    except:
        pass


class RefreshThemeCacheCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        """API entry point to rebuild main menu."""
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
                "children": self.create_menu(
                    "switch_theme", "*.sublime-theme")
            }]
        }]
        # save main menu to file
        with open(cache_path + "Main.sublime-menu", "w") as f:
            f.write(sublime.encode_value(menu, False))

    @staticmethod
    def create_menu(command, file_pattern):
        d = {}
        settings = sublime.load_settings("Theme-Switcher.sublime-settings")
        exclude_list = settings.get("themes_exclude", [])
        for path in sublime.find_resources(file_pattern):
            if not any(exclude in path for exclude in exclude_list):
                elems = path.split("/")
                # elems[1] package name
                # elems[-1] theme file name
                d.setdefault(elems[1], []).append(elems[-1])

        menu = [{
            "caption": package_name,
            "children": [{
                "caption": built_res_name(theme),
                "command": command,
                "args": {"name": theme}
            } for theme in sorted(
                themes, key=lambda x: x.replace(".", " "))]
        } for package_name, themes in sorted(d.items())]

        menu.append({"caption": "-", "id": "separator"})
        menu.append({"caption": "Refresh Theme Cache",
                    "command": "refresh_theme_cache"})
        return menu


class SwitchWindowCommandBase(sublime_plugin.WindowCommand):
    """Base class for SwitchThemeCommand and SwitchColorSchemeCommand."""

    def run(self, name=None):
        """API entry point for command execution."""
        if name:
            self.apply_setting(name)
        else:
            self.show_quick_panel()

    def apply_setting(self, name):
        """Directly apply the provided theme or color scheme."""
        if any(sublime.find_resources(os.path.basename(name))):
            settings_file = "Preferences.sublime-settings"
            sublime.load_settings(settings_file).set(self.KEY, name)
            sublime.save_settings(settings_file)
        else:
            sublime.status_message(name + " does not exist!")

    def show_quick_panel(self):
        """List all available themes or color schemes in a quick panel."""
        settings_file = "Preferences.sublime-settings"
        settings = sublime.load_settings(settings_file)
        names, values = self.get_items()
        current_value = settings.get(self.KEY)
        selected_index = self.get_selected(values, current_value)

        def on_select(index):
            if -1 < index < len(values):
                settings.set(self.KEY, values[index])
                sublime.save_settings(settings_file)
            elif current_value:
                settings.set(self.KEY, current_value)

        def on_highlight(index):
            settings.set(self.KEY, values[index])

        self.window.show_quick_panel(
            items=names, selected_index=selected_index,
            on_highlight=on_highlight, on_select=on_select)


class SwitchThemeCommand(SwitchWindowCommandBase):
    KEY = 'theme'

    @staticmethod
    def get_items():
        """Return a list of quick panel items for all themes.

        The values are the basename of each *.sublime-theme.

        NOTE: Excludes themes manipulated by zz File Icons as
              they are automatically created and used if required.
        """
        names = []
        values = []
        settings = sublime.load_settings("Theme-Switcher.sublime-settings")
        exclude_list = settings.get("themes_exclude", [])
        paths = sorted(
            sublime.find_resources("*.sublime-theme"),
            key=lambda x: os.path.basename(x))
        for path in paths:
            if not any(exclude in path for exclude in exclude_list):
                elems = path.split("/")
                # elems[1] package name
                # elems[-1] theme file name
                names.append(
                    [built_res_name(elems[-1]),    # title
                     "Package: " + elems[1]])      # description
                values.append(elems[-1])
        return [names, values]

    @staticmethod
    def get_selected(values, current_value):
        """Return the index of the currenty active theme in <values>."""
        try:
            selected_index = values.index(current_value)
        except ValueError:
            selected_index = -1
        return selected_index


class SwitchColorSchemeCommand(SwitchWindowCommandBase):
    KEY = 'color_scheme'

    @staticmethod
    def get_items():
        """Return a list of quick panel items for all color schemes.

        The values are the full path of each *.tmTheme.

        NOTE: Excludes color schemes manipulated by SublimeLinter as
              they are automatically created and used if required.
        """
        names = []
        values = []
        settings = sublime.load_settings("Theme-Switcher.sublime-settings")
        exclude_list = settings.get("colors_exclude", [])
        paths = sorted(
            sublime.find_resources("*.tmTheme"),
            key=lambda x: os.path.basename(x))
        for path in paths:
            if not any(exclude in path for exclude in exclude_list):
                elems = path.split("/")
                # elems[1] package name
                # elems[-1] color scheme file name
                names.append(
                    [built_res_name(elems[-1]),    # title
                     "Package: " + elems[1]])      # description
                values.append(path)
        return [names, values]

    @staticmethod
    def get_selected(values, current_value):
        """Return the index of the currenty active color scheme in <values>.

        If the color scheme is not contained by values it might have been
        automatically created and selected by SublimeLinter so we search
        for the original one and return its index.
        """
        try:
            selected_index = values.index(current_value)
        except ValueError:
            try:
                # find the original color scheme for a sublimelinter hacked
                original_scheme = current_value.replace(" (SL)", "")
                original_scheme = os.path.basename(original_scheme)
                original_scheme = sublime.find_resources(original_scheme)[-1]
                selected_index = values.index(original_scheme)
            except ValueError:
                selected_index = -1
        return selected_index
