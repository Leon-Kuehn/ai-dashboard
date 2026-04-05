FROM python:3.12-alpine

# Install psutil (requires build tools only during install)
RUN apk add --no-cache --virtual .build-deps gcc musl-dev linux-headers \
    && pip install --no-cache-dir psutil==6.1.1 \
    && apk del .build-deps

WORKDIR /app
COPY metrics_proxy.py .

# Run as nobody (UID 65534)
USER nobody

EXPOSE 9090

CMD ["python", "-u", "metrics_proxy.py"]
