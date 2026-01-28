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

# Run service
CMD ["python", "-m", "mcs_orchestrator.api.main"]

