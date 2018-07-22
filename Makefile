.PHONY: venv, setup, update

venv: requirements.txt
	@virtualenv venv -p python3
	@source venv/bin/activate && pip install -r requirements.txt	

setup:
	@source venv/bin/activate && python src/setup.py

data:
	@source venv/bin/activate && python src/data.py
