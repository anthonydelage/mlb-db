.PHONY: venv, setup, update

venv: requirements.txt
	@virtualenv venv -p python3
	@source venv/bin/activate && pip install -r requirements.txt	

tables:
	@source venv/bin/activate && python src/tables.py

data:
	@source venv/bin/activate && python src/data.py

statcast-latest:
	@source venv/bin/activate && python src/data.py --statcast --year=$(shell date +'%Y')