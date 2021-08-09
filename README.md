# AgMIP Submission

AgMIP Submission ("agmipsub") is a data submission application for AgMIP based on the Self-Contained Science App (SCSA) by @rcpurdue.

## Application Overview

The application allows the user to upload a data file to a project repository on MyGeoHub. During the submission process, the application will validate, clean, diagnose, and harmonize the data. The application also provides some data visualization functionalities, which the user can use to find outliers within their data. Upon successful submission, the application will merge the uploaded data with the existing dataset, which the user can access through a data exploration tool on MyGeoHub. 

The application expects the input file to meet these requirements:

1. File must be in CSV format
2. File must have at least the following columns, in any order: Scenario, Region, Variable/Indicator, Item/Sector, Unit, Year  

Example:

```
Scenario,Region,Variable,Item,Unit,Year,Value
"Scenario_1","REG","VAR","ITM","million",2001,1.23456
"Scenario_1","REG","VAR","ITM","million",2002,7.89012
...
```

## Development

### Code Structure

The AgMIP Submission tool is a Jupyter notebook-based application. We use ipywidgets to create the user interface widgets (menus, buttons, etc.).

The tool runs the agmip-submission.ipynb notebook. However, instead of storing most of the code in notebook cells, the notebook references external Python code. So, the majority of the logic resides in the Python files in the scripts subdirectory. The code follows the Model-View-Controller (MVC) pattern. That is, for simple organizational reasons, we split the application logic between the following modules:

- model.py: Manage application data or states
- view.py: Render user interface
- controller.py: Coordinate between model and view

For modularity reasons, we also create several domain abstractions to handle domain-specific or heavy data processing logic. These abstractions reside in the domain.py module. The interaction between these modules is set up based on the following layered architecture. 

<img width="601" alt="image" src="https://user-images.githubusercontent.com/42981908/128698708-0ec4e0cf-ca15-4941-b7ef-56a7a870abe7.png">

Then, this application comes with a few test suites, which reside in the tests/ subdirectory. 

### Environment

The tool is currently hosted on MyGeoHub. MyGeoHub is a website based on HUBzero. AgMIP Submission is, therefore, a HUBzero "tool." As such, supplementary files are required. This enforces most of the directory structure of this repository. It requires the src directory and unused Makefile. Also, it requires the invoke file in the middleware subdirectory.

### Building, Developing, and Testing

We recommend using an Anaconda environment. After creating and activating the conda environment (see environment.yml), run Jupyter notebook to start the notebook server. Then, use the local URLs displayed by that command to access and run the notebook using your browser. 

Note that during development, you can change the code in the .py files and refresh the notebook to test the changes. Also, note that for file upload to work, you need to run the notebook server from the project directory or the parent of the project directory. 
