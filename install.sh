#!/bin/bash

curl -L -o /tmp/terraform-azurerm-ai-installer.tar.gz "https://github.com/WodansSon/terraform-azurerm-ai-assisted-development/releases/latest/download/terraform-azurerm-ai-installer.tar.gz"
mkdir -p terraform-azurerm-ai-installer
tar -xzf /tmp/terraform-azurerm-ai-installer.tar.gz -C terraform-azurerm-ai-installer --strip-components=1

git submodule update --init --recursive

python -m venv venv-azurerm-development-automation
source venv-azurerm-development-automation/bin/activate
pip install -r requirements.txt
