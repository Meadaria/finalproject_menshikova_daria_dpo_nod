install:
	poetry install

project:
	poetry run python main.py

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python -m pip install dist/finalproject_menshikova_daria_dpo_nod-0.1.0-py3-none-any.whl

make lint:
	 poetry run ruff check .

 