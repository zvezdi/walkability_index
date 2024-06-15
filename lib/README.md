## Setup

### Setup python

First install Anaconda or MiniConda

```bash
conda create -n geo
conda activate geo
conda install geopandas
conda install mamba -c conda-forge # mamba resolves dependencies better that conda
mamba install leafmap xarray_leaflet -c conda-forge
mamba install sqlalchemy psycopg2 -c conda-forge # to use a database connection
```

### Second run

```bash
conda activate geo
```

```bash
conda deactivate
```

Run doctests
`python -m doctest -v  file.py`
