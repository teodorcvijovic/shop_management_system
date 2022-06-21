FROM python:3

RUN mkdir -p /opt/src/shop
WORKDIR /opt/src/shop

COPY shop/warehouse.py ./application.py
COPY shop/configurationWarehouse.py ./configurationWarehouse.py
COPY shop/models.py ./models.py
COPY shop/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

# project root folder
ENV PYTHONPATH="/opt/src/shop"

ENTRYPOINT ["python", "./application.py"]