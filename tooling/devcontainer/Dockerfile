# Stage: development container for Edgar AI

FROM python:3.11-slim

# Install system build tools and git (often needed for pip editable installs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (VS Code recommendation)
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && mkdir -p /home/$USERNAME/.cache/pip \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME

USER $USERNAME

# Default working directory—VS Code will mount the repository here
WORKDIR /workspace

# Pre-install hatch so dependency resolution inside the container is faster
RUN pip install --no-cache-dir --upgrade pip

# The actual code is mounted at runtime; dependencies will be installed by
# `postCreateCommand` specified in *devcontainer.json*.

CMD ["sleep", "infinity"]
