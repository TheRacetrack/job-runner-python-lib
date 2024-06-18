.PHONY: venv

venv:
	python3 -m venv venv &&\
	. venv/bin/activate &&\
	pip install --upgrade pip setuptools &&\
	pip install -r requirements.txt -r requirements-dev.txt &&\
	pip install -e .
	@echo Activate your venv:
	@echo . venv/bin/activate

test:
	cd tests && python -m pytest -vv --tb=short -ra $(test)

run-local:
	cd sample/dockerfiled &&\
	JOB_NAME=primer JOB_VERSION=0.0.1 python main.py

build-docker:
	cd sample/dockerfiled &&\
	racetrack_job_wrapper template Dockerfile Dockerfile.templated &&\
	docker buildx build -t sample-primer-job:latest -f Dockerfile.templated .

run-docker: build-docker
	docker run --rm -it --name sample-primer-job -p 7000:7000 sample-primer-job:latest

run-racetrack:
	racetrack deploy sample/dockerfiled
