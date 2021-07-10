import cProfile
import os
import sys

# Modify PATH so that the following imports work
sys.path.insert(0, os.path.dirname("scripts"))
from scripts.model import Model
from scripts.business import DataSpecification, DataCleaningService
    
# Init data spec
data_specification = DataSpecification()
data_specification.uploaded_filepath = (
    Model.WORKING_DIR.parent / "resources" / "submissions" / "output_GLOBIOM_AgMIP3_12mar2021.csv"
)
data_specification.load_file()
data_specification.delimiter = ","
data_specification.guess_header_is_included()
data_specification.guess_model_name_n_column_assignments()

def run_cleaning_service():
    data_cleaner = DataCleaningService(data_specification)
    data_cleaner.parse_data()

cProfile.run("run_cleaning_service()")
