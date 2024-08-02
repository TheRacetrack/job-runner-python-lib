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
pip install "git+https://github.com/TheRacetrack/job-runner-python-lib.git@master"
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

You can run it inside an API server (and provide a lot of extra features)
by calling `racetrack_job_wrapper.standalone.serve_job_class` function in your Python program,
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
- Serve empty API server, responding to liveness and readiness probes, while loading the Job
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

## Job configuration
You may tweak additional features of your job by specifying extra fields in a `job.yaml` manifest:

```yaml
jobtype_extra:
  max_concurrency: 1
  max_concurrency_queue: 10
  home_page: '/api/v1/webview'
```

Manifest YAML will be passed as environment variable to the Job by Racetrack's infrastructure plugin.
That's how this library can access this configuration.

### Concurrent requests cap
Maximum number of concurrent requests can be limited by `jobtype_extra.max_concurrency` field:
By default, concurrent requests are unlimited. Setting `max_concurrency` to `1` will make the job
process requests one by one. Overdue requests will be queued and processed in order.

Having such concurrency limits may cause some requests to wait in a queue.
If a throughput is higher than the job can handle, the queue will grow indefinitely.
To prevent that, you can set `jobtype_extra.max_concurrency_queue` to limit the queue size.
When the queue is full, the job will return `429 Too Many Requests` status code.

Example (1 request at a time, with up to 10 requests waiting in a queue):
```yaml
jobtype_extra:
  max_concurrency: 1
  max_concurrency_queue: 10
```

### Home page
You can configure the home page of your job.
Home page is the one you see when opening a job through the Dashboard or at the root endpoint.
By default, it shows the SwaggerUI page. Now you can change it, for instance, to a webview endpoint:
```yaml
jobtype_extra:
  home_page: '/api/v1/webview'
```

### Caller name
Setting environment variable `LOG_CALLER_NAME=true` allows you to keep record of a caller in the job's logs.
```dockerfile
ENV LOG_CALLER_NAME "true"
```
This will add caller identity (username or ESC name) to every log entry.

### Logging
To produce logs, use `logging` module inside your job:
```python
import logging
logger = logging.getLogger(__name__)

class JobEntrypoint:
    def perform(self):
        logger.info('something happened')
```

## Comparison with Python job type
This library has been originated from
[Python job type plugin](https://github.com/TheRacetrack/plugin-python-job-type).
If you need to recreate some of its features, take a look at the
[job Dockerfile template](https://github.com/TheRacetrack/plugin-python-job-type/blob/master/src/job-template.Dockerfile)
and do the same in your individual Job's Dockerfile.

In contrast to Python job type plugin, you directly call the utility functions in your code, you bind the things together.
This is opposed to a job type, where the framework calls your code.
This project transitions from a framework into a library, giving you more control.
