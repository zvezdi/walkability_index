require 'color'

COLORS = ['maroon', 'chocolate', 'orange', 'gold', 'yellowgreen', 'forestgreen', 'darkgreen']

def color_to_hex(color_name)
  case color_name.downcase
  when 'maroon'
    return '#800000'
  when 'chocolate'
    return '#d2691e'
  when 'orange'
    return '#ffa500'
  when 'gold'
    return '#ffd700'
  when 'yellowgreen'
    return '#9acd32'
  when 'forestgreen'
    return '#228b22'
  when 'darkgreen'
    return '#006400'
  else
    raise "Unknown color #{color_name}"
  end
end

# Function to interpolate between colors
def interpolate_color(start_color, end_color, t)
  start_rgb = Color::RGB.from_html(color_to_hex(start_color)).to_rgb
  end_rgb = Color::RGB.from_html(color_to_hex(end_color)).to_rgb

  r = start_rgb.red + (end_rgb.red - start_rgb.red) * t
  g = start_rgb.green + (end_rgb.green - start_rgb.green) * t
  b = start_rgb.blue + (end_rgb.blue - start_rgb.blue) * t

  Color::RGB.new(r, g, b)
end

# Function to get color based on value (0-100)
def color_for(value, colors)
  scaled_value = value.to_f * (colors.length - 1) / 100.0
  index = scaled_value.floor
  t = scaled_value - index

  start_color = colors[index]
  end_color = colors[index + 1] || colors[index]

  interpolated_color = interpolate_color(start_color, end_color, t)

  interpolated_color.html
end


def create_legend_html(colors)
  colors_string = colors.join(', ')

  legend_html = <<-HTML
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 20px; 
                background: linear-gradient(to right, #{colors_string});
                z-index: 9999; font-size: 14px;"
          onmousemove="showValue(event)" onmouseout="hideValue()">
    </div>
    <div style="position: fixed; 
                bottom: 30px; left: 50px; width: 200px; height: 20px; 
                background: white; color: black; text-align: center; z-index: 9999; font-size: 14px;">
                Walkability index
    </div>
    <div id="hoverValue" style="position: fixed; 
                bottom: 70px; left: 50px; width: 50px; height: 20px; 
                background: rgba(255, 255, 255, 0.8); color: black; text-align: center; z-index: 9999; font-size: 14px; display: none;">
    </div>
    <script>
        function showValue(event) {
            var element = document.querySelector('[onmousemove]');
            var rect = element.getBoundingClientRect();
            var offsetX = event.clientX - rect.left;
            var value = Math.round((offsetX / rect.width) * 100);
            var hoverValue = document.getElementById('hoverValue');
            hoverValue.style.left = (event.clientX + 10) + 'px';
            hoverValue.style.display = 'block';
            hoverValue.innerHTML = value;
        }
        function hideValue() {
            var hoverValue = document.getElementById('hoverValue');
            hoverValue.style.display = 'none';
        }
    </script>
  HTML

  legend_html
end

def popup(content_dict)
  html = <<~HTML
    <div style="border-radius: 5px; background-color: white;">
  HTML

  content_dict.each do |key, value|
    html += <<~HTML
      <div style="padding: 5px 0; display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 2rem;">
        <span style="font-weight: bold; white-space: nowrap;">#{key}:</span> <span style="white-space: nowrap;">#{value}</span>
      </div>
    HTML
  end

  html += <<~HTML
    </div>
  HTML

  html.strip
end
