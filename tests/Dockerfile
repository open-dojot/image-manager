FROM local/imagemanager:latest

WORKDIR /usr/src/app/tests
ADD . /usr/src/app/tests

RUN pip install -r requirements/test_requirements.txt

CMD ["python", "tests/db_fixture.py"]
