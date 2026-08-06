FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app
ENV PATH="/usr/local/bin:${PATH}"

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-cache

COPY . .
EXPOSE 80

ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "uvicorn", "recnavi.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]
