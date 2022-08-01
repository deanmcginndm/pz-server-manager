#!/bin/bash
echo "Running docker-entrypoint.sh:"
python3 manage.py collectstatic --no-input --clear
pip3 install -r requirements.txt
echo "Checking new requirements"
echo "Applying database migrations"
#python3 manage.py migrate
echo "Starting pz server"
pwd
./server-files/start-server.sh -cachedir=/pz/server-data -servername=anthesis-pzserver &
echo "Starting django dev server"
python3 manage.py runserver 0.0.0.0:8000

echo "Done entrypoint" && /bin/bash