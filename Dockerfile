FROM mambaorg/micromamba:latest

# Set the working directory
WORKDIR /app

# Copy environment file and install dependencies
COPY environment.yaml /tmp/environment.yaml
RUN micromamba create -y -n myenv --file /tmp/environment.yaml && \
    micromamba clean --all --yes

# Activate the environment for future commands
SHELL ["micromamba", "run", "-n", "myenv", "/bin/bash", "-c"]

# Set the correct library path so MariaDB Connector works
# ENV LD_LIBRARY_PATH="/opt/conda/envs/myenv/lib/mariadb:${LD_LIBRARY_PATH:-}"

RUN ln -s /opt/conda/envs/myenv/lib/mariadb/libmariadb.so.3 /opt/conda/envs/myenv/lib/libmariadb.so.3

# Ensure mariadb_config is available
RUN which mariadb_config || echo "mariadb_config not found"

# Install MariaDB using pip (again, to catch potential issues)
RUN pip install --no-cache-dir --upgrade mariadb>=1.1.12

# Copy the application code
COPY . ./src

ENTRYPOINT ["micromamba", "run", "-n", "myenv", "python", "./src/main.py"]
