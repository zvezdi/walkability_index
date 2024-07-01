require 'sinatra/base'
require 'pry'
require 'pg'
require 'json'
require 'dotenv/load'
require 'rgeo'
require 'rgeo/geo_json'

require_relative 'helpers'

class App < Sinatra::Base
  configure :production, :development do
    enable :logging
  end

  set :public_folder, 'public'

  require 'uri'

  configure do
    encoded_password = URI.encode_www_form_component(ENV['password'])
    connection_string = "postgresql://#{ENV['username']}:#{encoded_password}@#{ENV['host']}:#{ENV['port']}/#{ENV['dbname']}"
    conn = PG.connect(connection_string)
    set :db_connection, conn
    # set :rgeo_factory, RGeo::Geographic.spherical_factory(srid: 4326)
    # set :mercator_factory, RGeo::Geographic.simple_mercator_factory(srid: 4326)
  end

  COLORS = ['maroon', 'chocolate', 'orange', 'gold', 'yellowgreen', 'forestgreen', 'darkgreen']

  # Function to swap coordinates for various geometry types
  def swap_coordinates(geometry)
    case geometry
    when RGeo::Feature::Point
      geometry.factory.point(geometry.y, geometry.x)
    when RGeo::Feature::LineString, RGeo::Feature::LinearRing
      points = geometry.points.map { |point| geometry.factory.point(point.y, point.x) }
      geometry.factory.line_string(points)
    when RGeo::Feature::Polygon
      exterior_ring = swap_coordinates(geometry.exterior_ring)
      interior_rings = geometry.interior_rings.map { |ring| swap_coordinates(ring) }
      geometry.factory.polygon(exterior_ring, interior_rings)
    when RGeo::Feature::MultiPolygon
      polygons = geometry.map { |polygon| swap_coordinates(polygon) }
      geometry.factory.multi_polygon(polygons)
    else
      geometry
    end
  end

  get '/service_level_absolute' do
    db = settings.db_connection

    @admin_regions = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_gen_adm_regions_service_level_absolute").to_a.map do |region|
      geom = swap_coordinates(RGeo::GeoJSON.decode(region['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      region.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @ge_rajons = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_ge_service_level_absolute").to_a.map do |ge|
      geom = swap_coordinates(RGeo::GeoJSON.decode(ge['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      ge.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @residential_buildings = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_residentials_service_level_absolute").to_a.map do |building|
      geom = swap_coordinates(RGeo::GeoJSON.decode(building['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      building.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @colors = COLORS
    @legend_html = create_legend_html(COLORS)
    if params[:weighted] == "true" 
      if params[:pca] == "true"
        @colored_metric = 'weighted_service_index_pca' 
      else
        @colored_metric = 'weighted_service_index'
      end
    else
      if params[:pca] == "true"
        @colored_metric = 'service_index_pca' 
      else
        @colored_metric = 'service_index'
      end
    end
    print(params)
    erb :index, layout: :layout
  end

  get '/service_level_isochron' do
    db = settings.db_connection

    @admin_regions = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_gen_adm_regions_service_level_isochron").to_a.map do |region|
      geom = swap_coordinates(RGeo::GeoJSON.decode(region['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      region.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @ge_rajons = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_ge_service_level_isochron").to_a.map do |ge|
      geom = swap_coordinates(RGeo::GeoJSON.decode(ge['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      ge.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @residential_buildings = db.exec("SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) AS geojson, * FROM zvezdi_work.results_residentials_service_level_isochron").to_a.map do |building|
      geom = swap_coordinates(RGeo::GeoJSON.decode(building['geojson'], json_parser: :json))
      geojson = JSON.generate(geom)

      building.merge!({
        geom: geom,
        geojson: geojson,
      })
    end

    @colors = COLORS
    @legend_html = create_legend_html(COLORS)
    if params[:weighted] == "true" 
      if params[:pca] == "true"
        @colored_metric = 'weighted_service_index_pca' 
      else
        @colored_metric = 'weighted_service_index'
      end
    else
      if params[:pca] == "true"
        @colored_metric = 'service_index_pca' 
      else
        @colored_metric = 'service_index'
      end
    end
    print(params)
    erb :index, layout: :layout
  end
  
  
end
