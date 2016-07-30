Food Diary
============

Food Diary is web application for convenient creation of food orders among group of people from various restaurants.

### Run localy

To get started with the application you will need [docker to be installed]( https://docs.docker.com/engine/getstarted/step_one/#step-1-get-docker ) along with the [docker-compose](https://docs.docker.com/compose/install/).

Install necessary requirements inside of docker container:
```bash
$   docker-compose run django pip install -r requirements.txt
```

Run docker compose in a background:
```bash
$   docker-compose up -d
```

Install database migrations inside of docker container:
```bash
$   docker-compose run python foodorder/manage.py migrate
```

After that site is going to be available on 127.0.0.1:8000

