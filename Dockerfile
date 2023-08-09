FROM mambaorg/micromamba:1.4.3-bullseye-slim
COPY --chown=$MAMBA_USER:$MAMBA_USER . . 
RUN micromamba install -y -n base -c conda-forge -c city-modelling-lab -f requirements/base.txt && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN pip install --no-deps -e .

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]