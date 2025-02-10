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
from calendar import month_name

def plot(tif_path):
    shapefile_path = '/Users/tc/Downloads/Community_Plan_Areas/Community_Plan_Areas.shp'

    with rasterio.open(tif_path) as src:
        tif_meta = src.meta
        gdf = gpd.read_file(shapefile_path)
        gdf = gdf.to_crs(tif_meta['crs'])
        shapes = gdf.geometry.values
        tif_data_celsius, out_transform = mask(src, shapes, crop=True)

    tif_data_celsius = tif_data_celsius[0] - 273.15
    tif_data_celsius[(tif_data_celsius < 15) | (tif_data_celsius > 60)] = np.nan

    # Set up the plot
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    show(tif_data_celsius, transform=out_transform, ax=ax, cmap='jet', alpha=1)
    gdf.boundary.plot(ax=ax, linewidth=0.5, edgecolor='black')

    file_name = os.path.basename(tif_path)
    parts = file_name.split('_')
    datetime_part = parts[2]  # e.g., "20200814T1656"
    date_str, time_str = datetime_part.split('T')  # "20200814", "1656"
    year = date_str[0:4]
    month = date_str[4:6]
    day = date_str[6:8]
    hour = time_str[0:2]
    minute = time_str[2:4]
    month_name_str = month_name[int(month)]
    plot_title = f"{year} {month_name_str} {day} at {hour}:{minute}"


    ax.set_title(plot_title)
    ax.set_extent([-118.5, -118, 32.7, 34.9], crs=ccrs.PlateCarree())

    norm = Normalize(vmin=15, vmax=60)
    sm = ScalarMappable(cmap='jet', norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation='vertical', label='Temperature (°C)')
    cbar.ax.tick_params(labelsize=20)
    cbar.set_label('Temperature (°C)', fontsize=20)

    ax.set_aspect('equal', adjustable='datalim')
    plt.tight_layout()

    out_png = os.path.splitext(tif_path)[0] + ".png"
    plt.savefig(out_png, dpi=300)

if __name__ == "__main__":
    tif_path = '/Users/tc/Downloads/ECOSTRESS202009/12592_001_20200925T001530_0601_01.tif'
    plot(tif_path)
