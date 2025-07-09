import os

def get_template_context(request):
    theme = getattr(request.state, "theme", "default")

    themes_dir = os.path.join("templates", "themes")
    try:
        available_themes = [
            name for name in os.listdir(themes_dir)
            if os.path.isdir(os.path.join(themes_dir, name)) and
               os.path.isfile(os.path.join(themes_dir, name, "style.css"))
        ]
    except FileNotFoundError:
        available_themes = ["default"]

    return {
        "request": request,
        "theme": theme,
        "available_themes": available_themes
    }
