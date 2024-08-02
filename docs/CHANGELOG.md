# Changelog
All **user-facing**, notable changes will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
