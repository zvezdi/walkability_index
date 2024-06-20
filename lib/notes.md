# Build walkability index

## General approach:

1. Build index residential -> services:

```python
for residential in residential_buildings:
  for poi_type in poi_types:
    for poi_subtype in poi_subtypes:
      for poi_location in buffered!(locations_of_type_poi_subtype):
        if dist(pedestrian_network, residential, poi_location) < 1000:
          # Maybe consider appending it and take into account the quality/quantity of the services to adjust the weight later
          survised[residential.id][poi_type][poi_subtype] = poi_location.id
          break
```

2. Compute a single number (the pedestrian index) for each residential building with the precomputed values

3. Compute an index for the region
   3.1. Simple avg
   3.2. Weighted avg with appartment count

### For visualization

- add to each residential_buildings surviced_index computed with the provided wheights
- add to each region avg index and wheighted index values

## Reversed index(how much reach has each poi): poi -> #surviced_buildings, #surviced_appartments

```python
for poi_type in poi_types:
  for poi_subtype in poi_subtypes:
    for poi_location in locations_of_type_poi_subtype:
      for residential in buffered!(residential_buildings):
        if dist(pedestrian_network, residential, poi_location) < 1000:
          poi_location[surviced_buildings] += 1
          poi_location[surviced_appartments] += residential.appartments
```

### For visualization

- add to each poi #surviced_buildings, #surviced_appartments

## Pitfalls:

1. Accuracy

- Aproximate residential building with closesed node of the peredstian network
- Aproximate poi location with closesed node of the peredstian network
- The weights on the edges are some averages and do not take into account demograpics of the region and their adjusted speed