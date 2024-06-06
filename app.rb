require 'sinatra/base'

class App < Sinatra::Base
  configure :production, :development do
    enable :logging
  end

  get '/' do
    logger.info "loading data"
    @text = "text text"
    erb :hello
  end

end
