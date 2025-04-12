## Usage
1.
```bash
git clone https://github.com/fla1ddy/cafe_app
cd cafe_app/
```
2\. Create .env file with this content:
```
SECRET_KEY=randomlettersandnumbers123
```
3.
```bash
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
4.
```bash
cd consumer/
alembic revision --autogenerate -m "Make migrations"
alembic upgrade head
```
5.
```bash
cd ..
uvicorn producer.main:app --reload
uvicorn consumer.main:app --reload --port 8080
```
6.
```bash
cd consumer/
python consume.py
```

