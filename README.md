# Build Walkability Index - POC Lozenec

This project aims to build a walkability index for the Lozenec area. The project is divided into two parts: a Sinatra Ruby server and a collection of Python scripts for data preprocessing and storage.

Sinatra Ruby server is to be developed. To generate the html for the map you can currently use the pythonscript that uses folium

## Project Structure

- **Sinatra Ruby Server**: Located in the top directory, this part of the project serves the web application.
- **Python Scripts**: Located in the `lib` directory, these scripts are used to precompute data and store it in the database. The main entry point for the Python part is `main.py`.

## Setup Instructions

### Sinatra Ruby Server

1. **Install Ruby**: Follow the instructions to install Ruby from [ruby-lang.org](https://www.ruby-lang.org/en/documentation/installation/).
2. **Install Bundler**: Bundler is a dependency manager for Ruby. You can install it using the following command:

```bash
gem install bundler
```

3. **Install Dependencies**: Navigate to the top directory and run:

```bash
bundle install
```

4. **Start the server**

```bash
./run.sh
```

### Python Environment Setup

1. **Install Python**: Developed with Python 3.11
2. **Create and setup a Virtual Environment**:

```bash
python -m venv venv_geo
source venv_geo/bin/activate
pip install networkx geopandas sqlalchemy shapely tqdm sklearn numpy pandas
```

3. **Run doctests** (Make sure the `venv_geo` is activated)

```bash
python -m doctest -v lib/*.py
```

4. **.env file**

Copy `lib/.env.local` to `lib/.env` and make sure to update it accordingly

5. **Running the Python Scripts** (Make sure the `venv_geo` is activated)

You need to correct structures of tables in the database for this to work. READ THE CODE before running!

- To run the computations (This takes a while ...):

```bash
python lib/main.py
```

- To run map generation

There are several scripts that are prefixed with **visualize** that will generate a html file in `saves`. For example:

```bash
python lib/visualize_regions_and_residentials_score.py
```

## License

This project is licensed under the MIT License.
