import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))  # Add project directory to PATH so system can find the scripts
# package

from IPython.display import HTML

# This notebook is based on Self-Contained Science App
from scripts import model as scsa_model
from scripts import view as scsa_view
from scripts import controller as scsa_controller


def test_app():
    # Create MVC objects
    model = scsa_model.Model()
    view = scsa_view.View()
    ctrl = scsa_controller.Controller()  # 0=none 1=info 2=debug

    # Inform MVC objects of ea. other
    model.intro(view, ctrl)
    view.intro(model, ctrl)
    ctrl.intro(model, view)

    # Run the notebook
    ctrl.start()
    
    assert True

def display(a):
    pass

class JSAppModel:
    def init(self):
        self.NB_AUTH_TOKEN = None
        self.UA_FILENAME_LABEL_MODEL_ID = None 
    @classmethod
    def to_javascript(cls):
        pass

