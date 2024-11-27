# Changelog
All **user-facing**, notable changes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.17.0] - 2024-11-05
### Added
- Memory profiler (memray) can be enabled and managed at runtime by endpoints.
  The reports can be downloaded without the need for the Kubernetes operator to be involved in this process
  See [Memory profiler guide](./memory-profiler.md).

## [1.16.8] - 2024-10-23
### Added
- This package is published to PyPI and can be installed with `pip install racetrack_job_runner`.

## [1.16.6] - 2024-10-18
### Added
- Added Recordkeeper utilities functions to keep track of Recordkeeper's predecessor ID.

## [1.16.5] - 2024-08-28
### Fixed
- Fixed escaping newline characters in JOB_MANIFEST_YAML env variable.

## [1.16.4] - 2024-08-01
### Changed
- Job's metadata like name, version and manifest YAML are passed as environment variables: `JOB_NAME`, `JOB_VERSION` and `JOB_MANIFEST_YAML`.
  They should be either provided by infrastructure target or set manually.
  That means you no longer need to put
  ```dockerfile
  COPY ./job.yaml /project/job.yaml
  ENV JOB_NAME="{{ manifest.name }}"
  ENV JOB_VERSION="{{ manifest.version }}"
  ```
  in your Dockerfile.

## [1.16.3] - 2024-08-01
### Changed
- `racetrack_client` and `racetrack_commons` modules has been moved under `racetrack_job_wrapper` package
  to prevent conflicts with original `racetrack_client` package.

## [1.16.2] - 2024-07-30
### Changed
- `pydantic` package is no longer a direct dependency of this library.

## [1.16.1] - 2024-07-11
### Changed
- Third-party requirements of this library are no longer pinned to the exact version, but to `>=` instead.

## [1.16.0] - 2024-06-10
### Added
- Job runner can be installed locally as a Python library.
