# TODO: add "pip install requirements" and a prompt to add an api key
# maybe even make another .py file responsible only for updating the api key?
#!/bin/bash

# Name of the virtual environment
VENV_NAME="lolenv"

# Create the virtual environment
echo "Creating virtual environment..."
python -m venv $VENV_NAME

# Activate the virtual environment
echo "Activating virtual environment..."
source $VENV_NAME/bin/activate

# Update pip to latest version
echo "Updating pip..."
pip install --upgrade pip

# Install requirements from the requirements.txt file
echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo "Setup completed. Virtual environment '$VENV_NAME' is ready to use."

