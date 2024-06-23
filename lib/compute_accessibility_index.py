import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def compute_accessibility_index_weighed_sum(gdf_residentials, df_access_wheights, column_name):
  """
    column_name: string - The name of the accessibility index column in the resulting df
  """
  weights_map = df_access_wheights.set_index('subgroup_id')[['gr_weights', 'sgr_weights']].to_dict('index')
  df = gdf_residentials.copy()

  def calculate_service_level(row):
    total = 0
    for col in row.index:
      if col in weights_map:
        gr_weight = weights_map[col]['gr_weights']
        sgr_weight = weights_map[col]['sgr_weights']
        if pd.notna(row[col]) and row[col] > 0:
          total += float(gr_weight) * float(sgr_weight)
    return total

  df[column_name] = df.apply(calculate_service_level, axis=1)

  return df

def compute_accessibility_index_pca(gdf_residentials, df_access_weights, column_name):
  """
    column_name: string - The name of the accessibility index column in the resulting df
  """
  weights_map = df_access_weights.set_index('subgroup_id')[['gr_weights', 'sgr_weights']].to_dict('index')
  
  # Make a working copy and we need to adjust the features
  df = gdf_residentials.copy()

  amenity_columns = list(weights_map.keys())

  # Apply weights to the amenity counts
  for col in amenity_columns:
    if col in df.columns:
      df[col] = df[col] * weights_map[col]['gr_weights'] * weights_map[col]['sgr_weights']
    else:
      # When we work with a subset of the data some subtypes might not be present at all, but I still want then to appear in the features
      df[col] = 0
  
  # Make sure that if any building is not serviced by a type we still get 0 for the features can be analyzed
  df.fillna(0, inplace=True)

  # Standardize the weighted data and apply PCA
  scaler = StandardScaler()
  standardized_data = scaler.fit_transform(df[amenity_columns])
  pca = PCA()
  principal_components = pca.fit_transform(standardized_data)
  
  # Determine the number of components to retain (explained variance > 95%)
  explained_variance = np.cumsum(pca.explained_variance_ratio_)
  num_components = np.argmax(explained_variance >= 0.95) + 1
  
  # Use the selected principal components to compute the accessibility index
  pca_scores = principal_components[:, :num_components]
  raw_accessibility = np.sum(pca_scores, axis=1)
  
  # Normalize the raw accessibility score to a 0-100 scale
  max_raw_score = raw_accessibility.max()
  min_raw_score = raw_accessibility.min()
  df[column_name] = 100 * (raw_accessibility - min_raw_score) / (max_raw_score - min_raw_score)
  
  return df
