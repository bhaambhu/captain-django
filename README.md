# README

## To Run Locally

- After cloning this repository, create a virtual environment using ```virtualenv venv``` - this creates a virtul environment in the venv directory.
- Activate that virtualenv using ```source venv/bin/activate```
- Now you are inside the virtual environment. Verify python version and pip are working by checking ```pip --version```. Then do ```pip install -r requirements.txt``` and you will be good to go with this project.

## To Update Repository On Github

- Do a pip freeze to get the packages list into the requirements.txt file using ```pip freeze > requirements.txt```.

You can also use ```pip list``` and manually compare with the packages listed in the requirements.txt file.