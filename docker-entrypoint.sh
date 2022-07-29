#!/bin/bash
echo "Running docker-entrypoint.sh:"
python3 manage.py bower_install -F --allow-root --settings="project_zomboid_manager.settings" --pythonpath='/pz'
python3 manage.py collectstatic --no-input --clear
pip3 install -r requirements.txt
echo "Checking new requirements"
echo "Applying database migrations"
#python3 manage.py migrate
echo "Starting pz server"
sh ./pz/server-files/start-server.sh
echo "Starting django dev server"
python3 manage.py runserver 0.0.0.0:8000

echo "Done entrypoint" && /bin/bash