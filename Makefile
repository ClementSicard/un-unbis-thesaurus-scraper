BOLT_URL := bolt://localhost:7687
OUTPUT := ./downloads/output.json

run-neo4j:
	poetry run python main.py -v -o $(OUTPUT) --bolt_url $(BOLT_URL)

run:
	poetry run python main.py -v -o $(OUTPUT)
