black:
	python -m isort --sl --line-length 120 mp3splitter tests
	python -m black --line-length 120 mp3splitter tests

lint:
	python -m isort --sl --line-length 120 mp3splitter tests
	python -m black --line-length 120 mp3splitter tests
	python -m pylint mp3splitter tests