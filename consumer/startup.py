import os
import time
import subprocess
import psycopg2

def wait_for_postgres():
    print('Waiting for postgres...')
    while True:
        try:
            conn = psycopg2.connect('postgresql://postgres:postgres@postgres:5432/postgres')
            conn.close()
            print('PostgreSQL started')
            break
        except:
            time.sleep(1)

def run_migrations():
    print('Running migrations...')
    os.system('alembic revision --autogenerate -m "Make migrations"')
    os.system('alembic upgrade head')

def start_services():
    print('Starting services...')
    # Start FastAPI app in background
    subprocess.Popen(['uvicorn', 'consumer.main:app', '--host', '0.0.0.0', '--port', '8080', '--reload'])
    # Start consume.py
    os.system('python /app/consumer/consume.py')

if __name__ == '__main__':
    wait_for_postgres()
    run_migrations()
    start_services() 