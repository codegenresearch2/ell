from pydantic import BaseModel, Field
from typing import Any
import json

class ConfigModel(BaseModel):
    project: str = Field(default='ell')
    copyright: str = Field(default='2024, William Guss')
    author: str = Field(default='William Guss')
    extensions: list = Field(default=['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinxawesome_theme'])
    exclude_patterns: list = Field(default=['_build', 'Thumbs.db', '.DS_Store'])
    html_theme: str = Field(default="sphinxawesome_theme")
    pygments_style: str = Field(default="default")
    pygments_style_dark: str = Field(default="dracula")
    html_theme_options: dict = Field(default={
        "show_prev_next": True,
        "show_scrolltop": True,
        "main_nav_links": {
            "Docs": "index",
            "API Reference": "reference/index",
        },
        "extra_header_link_icons": {
            "Discord": {
                "link": "https://discord.gg/vWntgU52Xb",
                "icon": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" height="18" fill="currentColor"><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M524.5 69.8a1.5 1.5 0 0 0 -.8-.7A485.1 485.1 0 0 0 404.1 32a1.8 1.8 0 0 0 -1.9 .9 337.5 337.5 0 0 0 -14.9 30.6 447.8 447.8 0 0 0 -134.4 0 309.5 309.5 0 0 0 -15.1-30.6 1.9 1.9 0 0 0 -1.9-.9A483.7 483.7 0 0 0 116.1 69.1a1.7 1.7 0 0 0 -.8 .7C39.1 183.7 18.2 294.7 28.4 404.4a2 2 0 0 0 .8 1.4A487.7 487.7 0 0 0 176 479.9a1.9 1.9 0 0 0 2.1-.7A348.2 348.2 0 0 0 208.1 430.4a1.9 1.9 0 0 0 -1-2.6 321.2 321.2 0 0 1 -45.9-21.9 1.9 1.9 0 0 1 -.2-3.1c3.1-2.3 6.2-4.7 9.1-7.1a1.8 1.8 0 0 1 1.9-.3c96.2 43.9 200.4 43.9 295.5 0a1.8 1.8 0 0 1 1.9 .2c2.9 2.4 6 4.9 9.1 7.2a1.9 1.9 0 0 1 -.2 3.1 301.4 301.4 0 0 1 -45.9 21.8 1.9 1.9 0 0 0 -1 2.6 391.1 391.1 0 0 0 30 48.8 1.9 1.9 0 0 0 2.1 .7A486 486 0 0 0 610.7 405.7a1.9 1.9 0 0 0 .8-1.4C623.7 277.6 590.9 167.5 524.5 69.8zM222.5 337.6c-29 0-52.8-26.6-52.8-59.2S193.1 219.1 222.5 219.1c29.7 0 53.3 26.8 52.8 59.2C275.3 311 251.9 337.6 222.5 337.6zm195.4 0c-29 0-52.8-26.6-52.8-59.2S388.4 219.1 417.9 219.1c29.7 0 53.3 26.8 52.8 59.2C470.7 311 447.5 337.6 417.9 337.6z"/></svg>""",
                "type": "font-awesome",
                "name": "Discord",
            },
        },
        "logo_light": "_static/ell-wide-light.png",
        "logo_dark": "_static/ell-wide-dark.png",
    })

    class Config:
        json_encoders = {
            Any: lambda v: json.dumps(v, default=lambda o: o.__dict__)
        }

    def size(self):
        return len(self.json())

config = ConfigModel()


In this rewritten code, I have used Pydantic's BaseModel for validation and JSON serialization. I have also added a custom JSON encoder to handle BaseModel instances. The `size` method calculates the size of the JSON representation of the configuration.