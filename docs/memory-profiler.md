# Memory profiler
Memory profiler can be enabled and managed at runtime by endpoints to track down memory leaks in the Jobs.
After the profiler gets off, the report is saved, and it can be downloaded at one of the Job's endpoints. This is intended to remove the need for the Kubernetes operator to be involved in this process.
All steps can be done by a developer of a Job.
The Job can be instructed to turn the profile on and off, and to download the reports in various forms.

## Setup
First, to make the profiler available, you need to set this environment variable:
```
MEMRAY_PROFILER=true
```
If you're running it locally, you can call:
```shell
export MEMRAY_PROFILER=true
```
However, if you're deploying the job to Racetrack, here's how to set this env var in a manifest:
```yaml
name: python-job-profiled
...
runtime_env:
  MEMRAY_PROFILER: true
```

This will make the Job to **start the [memray](https://bloomberg.github.io/memray/overview.html) profiler at its startup, make sure to turn it off afterward**. 
This will also bring up new endpoints to manage it.

If you're running the job in Docker, set the write permissions to the job's main directory
by adding this to your Dockerfile:
```Dockerfile
RUN chmod -R a+rw /src/job/
```

## Endpoints

Check out SwaggerUI at the main page of a Job for more details and to call these endpoints in a convenient way. (All endpoints may be prepended with `/pub/job/JOB_NAME/JOB_VERSION/` prefix)

- `POST /api/v1/profiler/memray/start` - Starts the memray profiler session, if it's not started yet.
- `POST /api/v1/profiler/memray/stop` - Stops the memray profiler session and saves the report internally.
- `GET /api/v1/profiler/memray/report` - Downloads the memray report as a binary file, e.g. at http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/report. The profiler session should be stopped beforehand to get the full report.
- `GET /api/v1/profiler/memray/flamegraph` - Downloads the [Flame Graph report](https://bloomberg.github.io/memray/flamegraph.html) as an HTML file. You can open it directly in a browser, e.g. at http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/flamegraph
- `GET /api/v1/profiler/memray/stats` - Get the memray report statistics as a text file. You can open it directly in a browser, e.g. at http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/stats

Having the report file downloaded, you can make any other analysis on it.
See [what else you can do with the memray report](https://bloomberg.github.io/memray/tree.html).

## Example
A job [sample/memory-leak/job.py](../sample/memory-leak/job.py) has the memory leak on purpose.
Let's track it down with the memory profiler.

Start the job with the profiler enabled:
```shell
MEMRAY_PROFILER=true racetrack_job_runner run sample/memory-leak/job.py
```

Call the perform endpoint couple of times:
```shell
curl -X 'POST' \
  'http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/perform' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Now, stop the profiler session to make the Job save the report file.
```shell
curl -X 'POST' 'http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/stop'
```

You can view the Flame Graph report directly in a browser: http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/flamegraph
and locate the memory leak there.

Or you can download the binary report file from the Job.
```shell
curl http://0.0.0.0:7000/pub/job/JOB_NAME/JOB_VERSION/api/v1/profiler/memray/report --output memray-report.bin
```

and analyze it with various memray reporters:
```shell
pip install memray
memray tree memray-report.bin
# or
memray stats memray-report.bin
```
which contains the output like
```
🥇 Top 5 largest allocating locations (by size):
	- perform:.../sample/memory-leak/job.py:7 -> 22.888MB
	- get_data:<frozen importlib._bootstrap_external>:1187 -> 6.830MB
```

which correctly points us to the culprit at line 7 of `./sample/memory-leak/job.py`.