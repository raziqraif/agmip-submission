"""
Contains namespaces for various constants or utility methods
They are placed here for modularity reasons or to prevent circular imports between modules
@date Jun 30, 2021
"""
from enum import Enum


class VisualizationTab(Enum):
    """Enum for visualization tab's content"""

    VALUE_TRENDS = 0
    GROWTH_TRENDS = 1
    BOX_PLOT = 2


class Page:
    """Namespace for the pages in this app"""

    FILE_UPLOAD = 1
    DATA_SPECIFICATION = 2
    INTEGRITY_CHECKING = 3
    PLAUSIBILITY_CHECKING = 4
