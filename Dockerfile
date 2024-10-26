ARG MODE="slim"

FROM cgr.dev/chainguard/python:latest AS slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /build

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable

COPY ./src ./main.py /build/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable


FROM slim as fast
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable --extra fast

FROM ${MODE} as build

FROM cgr.dev/chainguard/python:latest as runtime
ARG MODE="slim"

WORKDIR /app
COPY --from=build /build/.venv /app

ENTRYPOINT ["/app/bin/main"]