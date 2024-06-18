from racetrack_job_wrapper.standalone import serve_job_class

from job import Job


def main():
    serve_job_class(Job)


if __name__ == '__main__':
    main()
