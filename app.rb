require 'sinatra/base'
require 'pry'

class App < Sinatra::Base
  configure :production, :development do
    enable :logging
  end

  require 'pg'

  before do
    @connection = PG.connect(
      host: "",
      port: "",
      dbname: "",
      user: "",
      password: ""
    )
  end

  after do
    @connection.close
  end

  get '/' do
    results = @connection.exec(
      <<~SQL
        SELECT jsonb_build_object(
          'type',       'Feature',
          'id',         id,
          'geometry',   ST_AsGeoJSON(ST_Transform(geom, 4283))::jsonb,
          'properties', to_jsonb(row) - 'id' - 'geom'
        ) as poi FROM (SELECT * FROM poi_schools) row;
      SQL
    )

    @pois = results.map do |poi|
      as_hash = JSON.parse(poi["poi"])
      properties = as_hash["properties"]
      json_geom = JSON.generate(as_hash["geometry"])
      as_hash["geometry"] = json_geom
      as_hash["properties"] = properties

      as_hash
    end

    erb :index
  end
  
end
