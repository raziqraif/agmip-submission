from __future__ import annotations # Delay the evaluation of undefined types


class Model:

    def __init__(self):
        # Import MVC classes here to prevent circular import problem
        from .controller import Controller
        from .view import View 

        self.view: View
        self.controller: Controller

    def intro(self, view: View, controller: Controller) -> None:       # type: ignore
        """Introduce MVC modules to each other"""
        self.view = view
        self.controller = controller
