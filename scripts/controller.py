from __future__ import annotations  # Delay the evaluation of undefined types


class Controller:
    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .model import Model 
        from .view import View 
        
        self.model: Model
        self.view: View

    def intro(self, model: Model, view: View) -> None:      # type: ignore
        """Introduce MVC modules to each other"""
        self.model = model
        self.view = view

    def start(self) -> None:
        """Load data, build UI"""
        self.view.display()
