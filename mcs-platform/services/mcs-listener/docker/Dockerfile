FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy source
COPY src/ ./src/
COPY ../../libs/contracts/ ./libs/contracts/

# Install contracts
RUN cd libs/contracts && pip install -e .

# Copy alembic config
COPY alembic.ini ./

# Run service (migrations will be run in startup script or manually)
CMD ["uvicorn", "mcs_listener.api.main:app", "--host", "0.0.0.0", "--port", "8001"]

