from IPython.core.display import display
from IPython.core.display import HTML
import ipywidgets as ui

display(
    HTML(
        """
        <script>
        
            // Format: <BASE_URL>/notebooks/<PATH_TO_CURRENT_NOTEBOOK>
            var NOTEBOOK_URL = window.location.href           
            var BASE_URL = NOTEBOOK_URL.split("/notebooks/")[0]
        </script>
        """
    )
)
