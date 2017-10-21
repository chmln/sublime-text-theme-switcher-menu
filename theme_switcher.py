import sublime
import sublime_plugin
import os

# Sublime Text 3127+ contains the ui.py
_HAVE_ST_UI = int(sublime.version()) >= 3127


def menu_cache_path():
    """Return absolute path for plugin's main menu cache dir."""
    return os.path.join(sublime.packages_path(), "User", "Theme-Switcher.cache")


def delete_cache():
    """Delete the menu cache folder to remove main menu items."""
    try:
        from shutil import rmtree
        rmtree(menu_cache_path())
    except OSError:
        pass


def built_res_name(pkg_name):
    """Built menu or quick panel item name from a resource file name."""
    name, _ = os.path.splitext(os.path.basename(pkg_name))
    return name.replace(" - ", " ").replace("-", " ").replace(".", " ")


def plugin_loaded():
    """Refresh cached Main.sublime-menu after plugin is loaded."""
    RefreshThemeCacheCommand().run()


def plugin_unloaded():
    """Clear cached Main.sublime-menu if the plugin is unloaded."""
    delete_cache()


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
                "children": self.create_menu(
                    "switch_theme", "*.sublime-theme", "themes_exclude")
            }]
        }]
        if _HAVE_ST_UI:
            # ST3127+ no longer provides its own "Color Scheme" sub menu.
            menu[0]["children"].insert(0, {
                "caption": "Color Scheme",
                "children": self.create_menu(
                    "switch_color_scheme", "*.tmTheme", "colors_exclude")
            })
        # save main menu to file
        cache_path = os.path.join(cache_path, "Main.sublime-menu")
        with open(cache_path, "w", encoding="utf-8") as menu_file:
            menu_file.write(sublime.encode_value(menu, False))

    @staticmethod
    def create_menu(command, file_pattern, exclude_setting):
        d = {}
        settings = sublime.load_settings("Theme-Switcher.sublime-settings")
        exclude_list = settings.get(exclude_setting, [])
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
            } for theme in themes]
        } for package_name, themes in sorted(d.items())]

        menu.append({"caption": "-", "id": "separator"})
        menu.append({"caption": "Refresh Theme Cache",
                    "command": "refresh_theme_cache"})
        return menu


class SwitchWindowCommandBase(sublime_plugin.WindowCommand):
    """Base class for SwitchThemeCommand and SwitchColorSchemeCommand."""

    PREFS_FILE = 'Preferences.sublime-settings'

    # A set of tuples (settings, original) with view specific color schemes or
    # themes which need to be restored after all as this command intends to
    # apply the global color scheme or theme only but applies preview to all
    # views no matter they use their own settings or not.
    overridden = set()

    # The last selected row index - used to debounce the search so we
    # aren't apply a new color scheme or theme with every keypress
    last_index = -1

    def run(self, name=None):
        """API entry point for command execution."""
        if name:
            self.apply_setting(name)
        else:
            self.show_quick_panel()

    def apply_setting(self, name):
        """Directly apply the provided theme or color scheme."""
        if any(sublime.find_resources(os.path.basename(name))):
            sublime.load_settings(self.PREFS_FILE).set(self.KEY, name)
            sublime.save_settings(self.PREFS_FILE)
        else:
            sublime.status_message(name + " does not exist!")

    def show_quick_panel(self):
        """List all available themes or color schemes in a quick panel."""
        settings = sublime.load_settings(self.PREFS_FILE)
        names, values = self.get_items()
        current_value = settings.get(self.KEY, self.DEFAULT)
        selected_index = self.get_selected(values, current_value)

        def on_select(index):
            # reset all view specific settings to initial values
            self.reset_overridden()
            # apply global settings
            if -1 < index < len(values):
                settings.set(self.KEY, values[index])
            else:
                settings.set(self.KEY, current_value)
            sublime.save_settings(self.PREFS_FILE)

        def on_highlight(index):
            if index == -1:
                return

            self.last_index = index

            def update_ui():
                if index != self.last_index:
                    return
                value = values[index]
                if settings.get(self.KEY) == value:
                    return
                # apply value to global settings
                settings.set(self.KEY, value)
                # apply value to overridden views
                if not self.overridden:
                    self.find_overridden(value)
                for view_setting, _ in self.overridden:
                    view_setting.set(self.KEY, value)

            sublime.set_timeout(update_ui, 250)

        self.window.show_quick_panel(
            items=names, selected_index=selected_index,
            on_highlight=on_highlight, on_select=on_select)

    def find_overridden(self, global_value):
        """Find view specific settings and their initial values."""
        return None

    def reset_overridden(self):
        """Reset view specific settings to their initial values."""
        self.overridden.clear()


class SwitchThemeCommand(SwitchWindowCommandBase):

    KEY = 'theme'
    DEFAULT = 'Default.sublime-theme'

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
        exclude_list = settings.get("themes_exclude") or []
        paths = sorted(
            sublime.find_resources("*.sublime-theme"),
            key=lambda x: os.path.basename(x).lower())
        for path in paths:
            if not any(exclude in path for exclude in exclude_list):
                parts = path.split("/")
                theme = parts[-1]
                # themes are merged by ST so display only first one
                if theme in values:
                    continue
                # parts[1] package name
                # parts[-1] theme file name
                names.append(
                    [built_res_name(theme),       # title
                     "Package: " + parts[1]])     # description
                values.append(theme)
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
    DEFAULT = 'Packages/Color Scheme - Default/Monokai.tmTheme'

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
        exclude_list = settings.get("colors_exclude") or []
        paths = sorted(
            sublime.find_resources("*.tmTheme"),
            key=lambda x: os.path.basename(x).lower())
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

    def find_overridden(self, global_cs):
        """Create a set of view specific color schemes and their defaults.

        Arguments:
            global_cs (string):
                the global color scheme from Preferences.sublime-settings

        Returns:
            tuple (settings, original)
             - settings (sublime.Settings): the view settings object
             - original (string): the original "color_scheme" for the view
        """
        project = self.window.project_data()
        pcs = project.get('settings', {}).get(self.KEY) if project else None
        for i in range(self.window.num_groups()):
            view = self.window.active_view_in_group(i)
            view_settings = view.settings()
            vcs = view_settings.get(self.KEY, self.DEFAULT)
            if pcs is not None:
                # view shows project specific setting
                # needs to be deleted after all
                if vcs == pcs and pcs != global_cs:
                    self.overridden.add((view_settings, None))
                    continue
            if vcs != global_cs:
                # view shows view specific setting
                # needs to be reset to default value after all
                self.overridden.add((view_settings, vcs))

    def reset_overridden(self):
        """Reset view specific settings to their initial values."""
        for settings, original in self.overridden:
            if original is None:
                # apply project specific values
                settings.erase(self.KEY)
            else:
                # apply view specific values
                settings.set(self.KEY, original)
        super().reset_overridden()


class SelectColorSchemeCommand(sublime_plugin.WindowCommand):
    """Hide ST core select_color_scheme command.

    This class is provided by the ui.py in the Default.sublime-package of
    Sublime Text 3127+. It intends to provide the functionality of this plugin
    by the core. Unfortunatelly it does neither provide filters nor does it
    handle color schemes of the SublimeLinter package.

    In order to provide consistent user experience, Theme Menu Switcher
    hides this command to avoid duplicated menu or command panel entries.
    It can still be called via run_command().
    """

    def is_visible(self):
        return False


class SelectThemeCommand(sublime_plugin.WindowCommand):
    """Hide ST core select_theme command.

    This class is provided by the ui.py in the Default.sublime-package of
    Sublime Text 3127+. It intends to provide the functionality of this plugin
    by the core. Unfortunatelly it does neither provide filters.

    In order to provide consistent user experience, Theme Menu Switcher
    hides this command to avoid duplicated menu or command panel entries.
    It can still be called via run_command().
    """

    def is_visible(self):
        return False
