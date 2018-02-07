FROM local/imagemanager:latest

WORKDIR /usr/src/app/tests
ADD . /usr/src/app/tests

RUN pip install -r test_requirements.txt

CMD ["python", "db_fixture.py"]
