# How to use Job Runner library
Job Runner library is intended to handle the calls to your Python function.
It will wrap it up in a web server.

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

## Features overview
The single call `serve_job_class(Job)` does a lot of things, including:

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

## Job standards
Job entrypoint classes should adhere to couple of standards to work properly with the Job Runner library.

Let's assume you already have your code in a repository at `supersmart/model.py`:
```python
import math

def is_prime(number: int) -> bool:
    """Check if a number is prime"""
    if number < 2:
        return False
    for i in range(2, int(math.sqrt(number)) + 1):
        if number % i == 0:
            return False
    return True
```

Now you need to make a few adjustments to adhere to job standards. 
Basically, you need to embed your code into an entrypoint class with `def perform` method.
Create `job_entrypoint.py`:
```python
from supersmart.model import is_prime

class JobEntrypoint:
    def perform(self, number: int) -> bool:
        """
        Check if a number is prime.
        :param number: The integer number to check.
        :return: Boolean whether the number is prime.
        """
        return self.is_prime(number)
```

This method will be called by when calling `/perform` endpoint on your job.
The parameters you declared in a `perform` method signature will be visible at `/parameters` endpoint. 
For example, `/parameters` response may look like:
```json
[
  {
    "name": "number",
    "type": "int"
  }
]
```

When calling `/perform` endpoint, pass the parameters as a JSON object:
```json
{
  "number": 7907,
}
```

### Input payload: `docs_input_example` method
Optionally, you can also add a `docs_input_example` method returning exemplary input values for your job.
It should return a dictionary mapping every parameter name to its sample value. 
That is an exemplary payload for your service (it will be seen in Swagger UI).
This should be the input giving not erroneous result so that it can be used by others to see how the entrypoint works.
For instance:
```python
def docs_input_example(self) -> dict:
    return {
        'number': 7907,
    }
```

### Auxiliary endpoints: `auxiliary_endpoints` method
If you need more callable endpoints, you can extend Job API with custom auxiliary endpoints (besides `/perform`).
Do it by implementing `auxiliary_endpoints` method in your entrypoint class, 
returning dict with endpoint paths and corresponding methods handling the request:
```python
def auxiliary_endpoints(self) -> dict[str, Callable]:
    """Dict of custom endpoint paths (besides "/perform") handled by Entrypoint methods"""
    return {
        '/explain': self.explain,
    }

def explain(self, x: float, y: float) -> dict[str, float]:
    """
    Explain feature importance of a model result.
    :param x: First element to add.
    :param y: Second element to add.
    :return: Dict of feature importance.
    """
    result = self.perform(x, y)
    return {'x_importance': x / result, 'y_importance': y / result}
```

If you want to define example data for your auxiliary endpoints,
you can implement `docs_input_examples` method returning 
mapping of Job's endpoints to corresponding exemplary inputs.
So it should return a dictionary of dictionaries (endpoint path -> parameter name -> parameter value).
You can even use it to define sample input data for the default entrypoint (`/perform` endpoint)
instead of using `docs_input_example` method to keep it concise.
Exemplary payloads will be visible in Swagger UI for corresponding endpoints.
It should be the input giving not erroneous result so that it can be used by others to see how the endpoint works.
For instance:
```python
def docs_input_examples(self) -> dict[str, dict]:
    """Return mapping of Job's endpoints to corresponding exemplary inputs."""
    return {
        '/perform': {
            'numbers': [40, 2],
        },
        '/explain': {
            'x': 1,
            'y': 2,
        },
    }
```

See [python-auxiliary-endpoints](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-auxiliary-endpoints) for an example.

### Static endpoints: `static_endpoints` method
You can configure static endpoints to expose your local files at particular path by your Job.
Do it by implementing `static_endpoints` method in your entrypoint class, 
returning dict with endpoint paths and corresponding file metadata. 
File metadata can be either just the filename (relative to the root of repository) 
or the tuple of filename and mimetype.
If mimetype is not given, it will be guessed based on the file.
Mimetype is needed for browsers to interpret the content properly.
```python
    def static_endpoints(self):
        """Dict of endpoint paths mapped to corresponding static files that ought be served."""
        return {
            '/xrai': 'xrai.yaml',
            '/manifest': ('job.yaml', 'application/x-yaml'),
            '/docs/readme': 'README.md',
        }
```

Whole directories can also be handled by `static_endpoints`
to serve recursively all of its content.

See [python-static-endpoints](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-static-endpoints) for an example.

### Custom Webview UI: `webview_app` method
You can expose user-defined webview pages in your job. 
Implement `def webview_app(self, base_url: str)` method in your entrypoint class.
`base_url` parameter is a base URL prefix where the webview app is exposed.
The method should return a WSGI application (eg. Flask and Django apps are compliant with that standard).
Here's an exemplary implementation:
```python
    def webview_app(self, base_url: str):
        """
        Create WSGI app serving custom UI pages
        :param base_url Base URL prefix where WSGI app is deployed.
        """
        app = Flask(__name__, template_folder='templates')

        @app.route(base_url + '/')
        def index():
            return render_template('index.html', base_url=base_url)

        @app.route(base_url + '/postme', methods=['POST'])
        def postme():
            return jsonify({"hello": request.json})

        return app.wsgi_app
```

The frontend app will be available at `/api/v1/webview/` endpoint.
If there is a `static` directory in your job repo, those resources will be available at `/webview/static/` endpoint.

See [python-ui-flask](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-ui-flask) for an example.

### Prometheus metrics
Customized Prometheus metrics can be exported by implementing `metrics` method in your entrypoint class.
It should return list of Metric objects consisting of:

- `name` (**required**) - Prometheus metric name,
- `value` (**required**) - float number,
- `description` (optional) - a string indicating the purpose of the metric,
- `labels` (optional) - dictionary of additional labels to differentiate the 
  characteristics of the thing that is being measured 
  (see [Prometheus Metric and Label naming](https://prometheus.io/docs/practices/naming/)).
```python
def metrics(self):
    return [
        {
            'name': 'job_is_crazy',
            'description': 'Whether your job is crazy or not',
            'value': random.random(),
            'labels': {
                'color': 'blue',
            },
        },
    ]
```

Your metrics will be exposed at `/metrics` endpoint along with the other generic ones 
(including number of calls, number of errors, duration of requests).

See [python-metrics](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-metrics) for an example.

### Environment variables
If you need to access specific env variables during job building, you can set them
by using `build_env` field in a manifest:
```yaml
build_env:
  DEBIAN_FRONTEND: 'noninteractive'
```

If you need to access specific env variables during job runtime, 
you can set them by using `runtime_env` field in a manifest:
```yaml
runtime_env:
  DJANGO_DEBUG: 'true'
  TORCH_MODEL_ZOO: zoo
```

When using your runtime vars, don't use the following reserved names: `PUB_URL`, `JOB_NAME`.

### Secret variables
If you need to set secret environment vars during building your job,
use `secret_build_env_file` field in a manifest 
and point it to the env file containing the secret env variables.
The secret file shouldn't be checked into source control.
It will be loaded from your local machine each time you deploy your job.

For instance, you can use it for installing pip dependencies from a private repository.

1. Refer to a secret file in a manifest:
```yaml
secret_build_env_file: .env.build
```
2. `.env.build` file should adhere to [".env" format](https://docs.docker.com/compose/env-file/#syntax-rules):
```
# Git username or email
GITLAB_USERNAME = 'username@example.com'
# Use read_repo access token instead of your password
GITLAB_TOKEN = "Pa55w0rD"
```
3. Then use these vars in `requirements.txt`:
```
git+https://${GITLAB_USERNAME}:${GITLAB_TOKEN}@github.com/racetrack/ml-labs/mllab-utils.git
```
Since the `.env.build` file is not included in git repository, 
every new user cloning your repository will have to recreate this file.
We recommend to use `.env.build.dist` file as a template in repository, copy from it and fill it out before deploying a job.

Runtime secret variables are handled correspondingly by `secret_runtime_env_file` field in a manifest.

When the same env var name appears in both `build_env`/`runtime_env`
and in secrets (`secret_build_env_file`/`secret_runtime_env_file`), 
secret values take precedence before the former ones (overwrites them).

See [python-env-secret](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-env-secret) for an example.

### Public endpoints
To expose selected job endpoints to the public (to be accessible without authentication)
include them in the `public_endpoints` field in a manifest.
Every endpoint opens access to an exact specified path as well as all subpaths starting with that path.
Use short path endings without `/pub/job/.../` prefix:
```yaml
public_endpoints:
  - '/api/v1/perform'
  - '/api/v1/webview'
```

!!! warning
    Exempting a path `/foo` also exempts *any* path under it like `/foo/secret`. Use this feature with care.

After deploying such job, there will be created a request that needs to be approved by Racetrack admin.
Such approval needs to be done once for every new job version (with distinct `version` field).

See [python-ui-flask](https://github.com/TheRacetrack/plugin-python-job-type/tree/master/sample/python-ui-flask) for an example.

### Home page
You can configure the home page of your job.
Home page is the one you see when opening a job through the Dashboard or at the root endpoint.
By default, it shows the SwaggerUI page. Now you can change it, for instance, to a webview endpoint:
```yaml
jobtype_extra:
  home_page: '/api/v1/webview'
```

### Logging
To produce logs, use `logging` module inside your job:
```python
import logging
logger = logging.getLogger(__name__)

class JobEntrypoint:
    def perform(self):
        logger.info('something happened')
```

### Caller name
Setting `LOG_CALLER_NAME` in a manifest allows you to keep record of a caller in the job's logs:
```yaml
runtime_env:
  LOG_CALLER_NAME: 'true'
```
This will add caller identity (username or ESC name) to every log entry.

### Concurrent requests cap
Maximum number of concurrent requests can be limited by `jobtype_extra.max_concurrency` field:
By default, concurrent requests are unlimited. Setting `max_concurrency` to `1` will make the job
process requests one by one. Overdue requests will be queued and processed in order.

Having such concurrency limits may cause some requests to wait in a queue.
If a throughput is higher than the job can handle, the queue will grow indefinitely.
To prevent that, you can also set `jobtype_extra.max_concurrency_queue` to limit the queue size.
When the queue is full, the job will return `429 Too Many Requests` status code.

Example (1 request at a time, with up to 10 requests waiting in a queue):
```yaml
jobtype_extra:
  max_concurrency: 1
  max_concurrency_queue: 10
```

## Summary of principles
To sum up:

1. You MUST import your entrypoint class and call it with
   `racetrack_job_wrapper.standalone.serve_job_class` or `racetrack_job_wrapper.standalone.serve_job_instance` function.
1. The entrypoint class MUST have `def perform(self, ...)` method with any arguments.
1. You SHOULD use type annotations and meaningful names for `perform` arguments.
1. You MAY use named arguments or optional parameters (with default value) in a `perform` method signature.
1. You MUST NOT use `*args` in a `perform` method signature.
1. You SHOULD add docstring to a `perform` method that describes its parameters and return values.
1. You MAY do some initialization in `def __init__(self)` (eg. loading pickled model).
1. You MAY fetch some data during initialization and keep them in a working directory 
   (eg. load model data from external sources). Working directory is the root of your git repository.
1. You SHOULD use relative path `./file.txt` (instead of abs like `/src/job/file.txt`) 
   when accessing your model data.
1. You MAY put some required Python packages to `requirements.txt` file
   and refer to it in a Dockerfile.
1. You MUST NOT refer to some local files that are not pushed to the repository. 
   Keep in mind that your job is built from your git repository.
1. You SHOULD implement `docs_input_example` method that returns an example input payload for your job.
1. You MAY implement `auxiliary_endpoints` method pointing to the methods handling your custom endpoint paths. 
1. You MAY implement `static_endpoints` method to serve static files. You SHOULD specify mimetype for them.
1. You MAY implement `metrics` method to export your custom Prometheus metrics at `/metrics` endpoint.
1. You MAY configure environment variables applied on build time and runtime by setting them explicitly or through a secret file.
1. The Job application MUST be stateless. It MUST NOT depend on previous requests.
