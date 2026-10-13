test:
	pytest -q

lint:
	# Add linting later

api:
	uvicorn sp_platform.api:app --reload

web:
	cd web && npm run dev

check: test
