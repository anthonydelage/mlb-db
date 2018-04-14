.PHONY: venv, db, update

venv: requirements.txt
	@virtualenv venv -p python3
	@source venv/bin/activate && pip install -r requirements.txt	

db: venv
	@source venv/bin/activate && python src/db.py

update: venv
	@source venv/bin/activate && python src/update.py
