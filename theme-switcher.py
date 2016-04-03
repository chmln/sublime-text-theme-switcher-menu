import sublime
import sublime_plugin
import os
import sys
import json
import zipfile

MENU_BASE = """
[
    {
        "id": "preferences",
        "children":
        [{
            "caption": "Theme",
            "id": "themes"
        }]
    }
]
""".strip()

INST_PKGS_PATH = os.path.join(
    os.path.dirname(sublime.packages_path()), "Installed Packages"
);

PKG_FOLDER = os.path.join(sublime.packages_path(), "Theme-Switcher")
THEMES_MENU = os.path.join(PKG_FOLDER, "Main.sublime-menu")

def init():   

    if not os.path.isdir(PKG_FOLDER):
        os.makedirs(PKG_FOLDER)
    
    if not os.path.isfile(THEMES_MENU):
        open(THEMES_MENU, "w").close()
    
    menu = json.loads(MENU_BASE)
    menu[0]['children'][0]['children'] = create_menu()
    with open(THEMES_MENU,"w") as f:
        f.write(json.dumps(menu,indent=4))


def create_menu():

    menu = []
    packages = sorted(list(os.listdir(INST_PKGS_PATH)))

    for theme in packages:
        pkg = zipfile.ZipFile(os.path.join(INST_PKGS_PATH,theme))
        sub_themes = list(map(parsePkgName, filter(is_theme, pkg.namelist())))
        if sub_themes:
            menu.append({
                'caption': parsePkgName(theme),
                'children': [{

                    "caption":sub_theme, 
                    "command":"switchtheme", 
                    "args": {"name":sub_theme+".sublime-theme"}
                    } for sub_theme in sorted(sub_themes)]
            })

    menu.append({"caption": "-", "id": "separator"});    
    menu.append({"caption": "Refresh Theme Cache", "command": "refresh"})

    return menu

def is_theme(name):
    return "sublime-theme" == name.split('.')[-1]

def parsePkgName(pkg_name):
    return pkg_name.replace("." + pkg_name.split('.')[-1],"")
   
def plugin_loaded(): init()
def plugin_unloaded(): os.remove(THEMES_MENU)
    
class switchthemeCommand(sublime_plugin.WindowCommand):
    def run(self,name):
        settings = sublime.load_settings("Preferences.sublime-settings")
        settings.set('theme', name )
        sublime.save_settings("Preferences.sublime-settings")

class refreshCommand(sublime_plugin.WindowCommand):
    def run(self): init()