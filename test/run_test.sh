#!/bin/bash
coverage erase
sudo coverage run -p login.py
sudo coverage run -p dir.py
sudo coverage run -p file.py
coverage combine
coverage html
