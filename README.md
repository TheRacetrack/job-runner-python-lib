# Racetrack Job Runner library

This is a Python library that takes the Racetrack job and allows to run it in an API server.
This runner (aka "wrapper") embeds given Python class in a REST server and adds extra features.

The library can be imported and run locally without using Racetrack services at all.
Nevertheless, it is compatible with Racetrack standards and to run it there,
you can pack your Job into a Dockerfile and deploy it to Racetrack, using
[generic "dockerfile" job type](https://github.com/TheRacetrack/plugin-dockerfile-job-type).
Moreover, the outcome Docker image is nothing special, but just a regular API server.
It can be tested locally and deployed anywhere else.

Check out [Changelog](./docs/CHANGELOG.md) to find out about notable changes.

## Installation
You can locally install this Job runner to your local environment by doing:
```sh
pip install "git+https://github.com/TheRacetrack/job-runner-python-lib.git@master#subdirectory=."
```

This will install `racetrack_job_wrapper` package that can be imported later on.

## Sample job
See a [sample dockerfile job](./sample/dockerfiled) using this library in action.

Assuming you have a Job class like this:  
#### **`job.py`**
```python
import math

class Job:
    def perform(self, number: int) -> bool:
        """Check if a number is prime"""
        if number < 2:
            return False
        for i in range(2, int(math.sqrt(number)) + 1):
            if number % i == 0:
                return False
        return True

    def docs_input_example(self) -> dict:
        """Return example input values for this model"""
        return {'number': 7907}
```

You can run it inside an API server (and provide a lot of extra features) by calling `racetrack_job_wrapper.standalone.serve_job_class` function in your Python program,
combined with your `Job` class:  
#### **`main.py`**
```python
from racetrack_job_wrapper.standalone import serve_job_class
from job import Job

def main():
    serve_job_class(Job)

if __name__ == '__main__':
    main()
```

This will run your Job at `0.0.0.0:7000`.

This single line `serve_job_class(Job)` does a lot of things, including:

- Serve a Job at HTTP API server
- Serve automatically generated SwaggerUI documentation
- Measure and serve Prometheus metrics at `/metrics` endpoint, reporting:
  - how many times the job was called
  - how long it took to call the job
  - how many errors have occurred
- Map Job's methods to auxiliary endpoints
- Serve static resources
- Serve Custom Webview UI (if defined in a Job's entrypoint)
- Concurrent requests cap
- Make chain calls to other jobs
- Structured logging
- Keep record of a caller in the logs
- Show exemplary input payload in documentation (if defined in a Job's entrypoint)

## Running modes
### 1. Run on localhost
```shell
cd sample/dockerfiled
export JOB_NAME=primer JOB_VERSION=0.0.1
python main.py
```

### 2. Run in Docker
```shell
make run-docker
```

### 3. Run on Racetrack
```shell
racetrack deploy sample/dockerfiled
```

## Comparison with Python job type
This library has been originated from [Python job type plugin](https://github.com/TheRacetrack/plugin-python-job-type).
If you need to recreate some of its features, take a look at the [job Dockerfile template](https://github.com/TheRacetrack/plugin-python-job-type/blob/master/src/job-template.Dockerfile) and do the same in your individual Job's Dockerfile.

In contrast to Python job type plugin, you directly call the utility functions in your code, you bind the things together.
This is opposed to a job type, where the framework calls your code.
This project transitions from a framework into a library, giving you more control.
