# Multi-stage build: compile the venv in `builder`, ship only the runtime
# artifacts in the final image (no compilers, no pip cache, non-root user).

FROM python:3.12-slim AS builder
WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /data && chown appuser:appuser /data
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY monitoring.py ./

# /data is where the SQLite volume (docker-compose's envmon-data) is mounted;
# it must be owned by appuser *before* the first `docker compose up` creates
# the named volume, since Docker seeds a new volume's ownership from the
# image directory it's mounted over.
VOLUME /data

USER appuser
ENTRYPOINT ["python"]
CMD ["monitoring.py", "--help"]
