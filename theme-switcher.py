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
    menu=[]
    d={}

    for theme_path in sublime.find_resources("*.sublime-theme"):
        dirname,group,theme_name=theme_path.split("/")
        d.setdefault(group,[]).append(theme_name)

    for theme_group in sorted(d.keys()):
        menu.append({
            'caption': theme_group,
            'children': [{
                "caption":parsePkgName(theme), 
                "command":"switchtheme", 
                "args": {"name":theme}
                } 
            for theme in sorted(d[theme_group],key=lambda x:x.replace("."," "))]
        })

    menu.append({"caption": "-", "id": "separator"});    
    menu.append({"caption": "Refresh Theme Cache", "command": "refresh"})

    return menu


def parsePkgName(pkg_name):
    return pkg_name.replace("." + pkg_name.split('.')[-1],"")
   
def plugin_loaded(): 
    init()

def plugin_unloaded(): 
    os.remove(THEMES_MENU)
    
class switchthemeCommand(sublime_plugin.WindowCommand):
    def run(self,name):
        sublime.load_settings("Preferences.sublime-settings").set('theme', name)
        sublime.save_settings("Preferences.sublime-settings")

class refreshCommand(sublime_plugin.WindowCommand):
    def run(self): 
        init()