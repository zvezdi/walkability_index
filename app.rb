require 'sinatra/base'
require 'pry'

class App < Sinatra::Base
  configure :production, :development do
    enable :logging
  end

  require 'pg'

  before do
    @connection = PG.connect(
      host: "34.118.61.196",
      port: "5432",
      dbname: "ragis",
      user: "student",
      password: "extr3m3conditions"
    )
  end

  after do
    @connection.close
  end

  get '/' do
    # conn = db_connect
    results = @connection.exec(
      <<~SQL
        SELECT id, ST_AsGeoJSON(ST_Transform(geom, 4283))::json as coord, object_nam as poi_name, adres as address
        FROM poi_schools
      SQL
      # <<~SQL
      #   SELECT jsonb_build_object(
      #     'type',       'Feature',
      #     'id',         id,
      #     'geometry',   ST_AsGeoJSON(ST_Transform(geom, 4283))::jsonb,
      #     'properties', to_jsonb(row) - 'id' - 'geom'
      #   ) FROM (SELECT * FROM poi_schools) row;
      # SQL
    )
    # db_disconnect(conn)

    @pois = results
    # .map do |poi|
    #   {
    #     id: poi["id"],
    #     coord: JSON.parse(poi["coord"]),
    #     poi_name: poi["poi_name"],
    #     address: poi["address"]
    #   }
    # end
    # binding.pry

    erb :index
  end
  
end
