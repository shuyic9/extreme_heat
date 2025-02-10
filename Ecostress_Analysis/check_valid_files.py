import os
import glob
import csv
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
import geopandas as gpd
import numpy as np

def calculate_plot_perspective_ratio(tif_path, shapefile_path):
    try:
        with rasterio.open(tif_path) as src:
            tif_meta = src.meta

            # Read and reproject the shapefile to match the raster's CRS
            gdf = gpd.read_file(shapefile_path)
            gdf = gdf.to_crs(tif_meta['crs'])
            shapes = gdf.geometry.values

            # Mask the raster using the shapefile (crop to the bounding box)
            tif_data, out_transform = mask(src, shapes, crop=True)
    except ValueError as ve:
        # Skip files whose shapes do not overlap the raster
        if "Input shapes do not overlap raster" in str(ve):
            print(f"Skipping {os.path.basename(tif_path)}: {ve}")
            return None
        else:
            raise

    # Assume the raster has a single band; remove the band dimension.
    data = tif_data[0]

    # Convert from Kelvin to Celsius
    data_celsius = data - 273.15

    # Apply valid temperature range: set values outside 15–60 °C to NaN.
    data_celsius[(data_celsius < 15) | (data_celsius > 60)] = np.nan

    # Create a boolean mask for the polygon area:
    # True for pixels inside the polygon, False for those outside.
    poly_mask = geometry_mask(
        shapes,
        transform=out_transform,
        invert=True,
        out_shape=data_celsius.shape
    )

    # Compute the number of pixels inside the polygon.
    total_polygon_pixels = np.count_nonzero(poly_mask)

    # Compute the number of valid pixels inside the polygon.
    valid_pixels = np.count_nonzero(poly_mask & ~np.isnan(data_celsius))

    if total_polygon_pixels == 0:
        return None

    # Return the ratio of valid pixels (as seen in the plot)
    return valid_pixels / total_polygon_pixels

def extract_time_from_filename(filename):
    """
    Extracts the time from a filename with the pattern:
    <id>_<id>_<date>T<time>_<...>.tif
    For example, for '12531_003_20200920T184818_0601_01.tif',
    it returns '18:48'.
    """
    parts = filename.split('_')
    if len(parts) < 3:
        return ""
    datetime_part = parts[2]  # e.g., "20200920T184818"
    try:
        _, time_str = datetime_part.split('T')
        # Extract the first four digits for HHMM and format as HH:MM.
        formatted_time = time_str[:2] + ":" + time_str[2:4]
        return formatted_time
    except Exception as e:
        return ""

def main():
    # Folder containing TIFF files
    tif_folder = '/Users/tc/Downloads/EcostressProject/ECOSTRESS_202008'
    # Path to the shapefile
    shapefile_path = '/Users/tc/extreme_heat/County_Boundary/Planning_Areas_(LA_County_Planning).shp'
    
    # Get list of all TIFF files in the folder
    tif_files = glob.glob(os.path.join(tif_folder, '*.tif'))
    
    # List to store summary results for files with ratio > 0.75
    summary = []
    
    # Loop through each TIFF file and calculate the ratio
    for tif_path in tif_files:
        ratio = calculate_plot_perspective_ratio(tif_path, shapefile_path)
        filename = os.path.basename(tif_path)
        if ratio is not None:
            print(f"{filename}: {ratio:.2%}")
            if ratio > 0.75:
                time_str = extract_time_from_filename(filename)
                summary.append({
                    'filename': filename,
                    'valid_ratio': ratio,
                    'time': time_str
                })
        else:
            print(f"{filename}: Skipped or no pixels found inside polygon.")
    
    # Output CSV file with the summary of files meeting the threshold.
    csv_path = os.path.join(tif_folder, 'county_ratio_summary.csv')
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'valid_ratio', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)
    
    print(f"CSV summary written to {csv_path}")

if __name__ == "__main__":
    main()
