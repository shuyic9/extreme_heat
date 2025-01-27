import rasterio
import os
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from rasterio.mask import mask
from rasterio.plot import show
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


tif_path = '/Users/tc/Downloads/EcostressProject/ECOSTRESS_202008/11799_001_20200804T1329_0601_01.tif'
shapefile_path = '/Users/tc/extreme_heat/LA_County_Boundary/County_Boundary.shp'


src = rasterio.open(tif_path)
tif_data = src.read(1)
tif_meta = src.meta


gdf = gpd.read_file(shapefile_path)
gdf = gdf.to_crs(tif_meta['crs'])

# Clip the GeoTIFF using the shapefile geometries
shapes = gdf.geometry.values
tif_data_celsius, out_transform = mask(src, shapes, crop=True)
tif_data_celsius = tif_data_celsius[0] - 273.15  # convert kelvin to celsius

# Limit to display only the area from 15 to 60 degrees Celsius, and set pixel values outside the range to NaN
tif_data_celsius[(tif_data_celsius < 15) | (tif_data_celsius > 60)] = np.nan


fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
show(tif_data_celsius, transform=out_transform, ax=ax, cmap='jet', alpha=1)
gdf.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black')
file_name = os.path.basename(tif_path)
ax.set_title(file_name)


ax.set_extent([-118.5, -118, 32.7, 34.9], crs=ccrs.PlateCarree())
# if zoom in to the main LA county area use the extent below
# ax.set_extent([-118.5, -118, 33.6, 34.9], crs=ccrs.PlateCarree())

norm = Normalize(vmin=15, vmax=60)
sm = ScalarMappable(cmap='jet', norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, orientation='vertical', label='Temperature (°C)')
cbar.ax.tick_params(labelsize=20)
cbar.set_label('Temperature (°C)', fontsize=20)
ax.set_aspect('equal', adjustable='datalim')


plt.tight_layout()
plt.show()