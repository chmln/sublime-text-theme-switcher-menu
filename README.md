# Sublime Theme Switcher

**Painless theme selection in Sublime Text.**

Preview and choose themes using the command palette - <kbd>Ctrl+Shift+P</kbd> and type:
- `UI: Select Theme`
- `UI: Select Color Scheme`

![rec](https://cloud.githubusercontent.com/assets/11352152/22135694/de217a9e-de9d-11e6-8d7a-551f9b460c4f.gif)


Or just navigate to the `Preferences -> Theme`  menu.

![scr](https://cloud.githubusercontent.com/assets/11352152/14230693/b6e33c28-f92f-11e5-8d6c-b2e32054f804.png)

## Motivation

Looking up and remembering `SomeTheme-Variant.sublime-theme` values for every single theme is cumbersome. 

It is a replacement for the built-in `UI: Select Theme` and `UI: Select Color Scheme` commands of Sublime Text 3127+, which do not support SublimeLinter and don't allow to hide unwanted color schemes or themes from the selection lists.


## Settings

Some plugins dynamically create themes or color schemes which are not meant to
be selected by a user. To hide those you can create a settings file
`Theme-Switcher.sublime-settings` and add the pathes to `"colors_exclude"` or
`"themes_exclude"` filter lists.

```js
{
	"colors_exclude":
	[
		"Packages/User/SublimeLinter",
		"Packages/User/Sublimerge"
	],
	"themes_exclude":
	[
		"Packages/zzz A File Icon zzz/"
	]
}
```

## Credits

Credits to [@geekpradd](https://github.com/geekpradd) for idea and plugin structure.
