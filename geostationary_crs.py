"""Build a cartopy CRS for the FCI-MTG L1C geostationary projection.

`ccrs.Projection(crs_wkt)` (even with a BBOX added, see fix_crs_wkt.py) fails for
this data with a shapely `TopologicalError: An input LineString must be valid.`
The generic `Projection` class builds its plot boundary by forward-projecting the
*rectangular* corners of the CRS's lon/lat BBOX. For a full-disk geostationary
view, visibility is elliptical, not rectangular in lon/lat -- a BBOX corner like
(lat=81.2, lon=81.2) simultaneously is not actually visible from the satellite,
so projecting it produces a self-intersecting boundary ring.

`ccrs.Geostationary` is cartopy's dedicated class for this exact projection: it
computes the boundary analytically as an ellipse, so no BBOX is involved at all.
This builds it directly from the CF grid-mapping attributes, using cf-xarray to
locate the grid-mapping variable (`ds.cf.grid_mapping_names`) instead of assuming
it's called `spatial_ref` -- that name isn't part of the CF convention, just this
dataset's choice. `pyproj.CRS.from_cf()` builds the same CRS from those attrs
(confirmed to produce an identical WKT here), but going through a proj4 dict to
pull out individual parameters is a lossy round-trip pyproj itself warns about,
so we read the CF attributes directly instead.
"""

import cartopy.crs as ccrs
import cf_xarray  # noqa: F401 registers the .cf accessor
import xarray as xr


def geostationary_crs(ds: xr.Dataset) -> ccrs.Geostationary:
    """Return a cartopy `Geostationary` CRS matching `ds`'s grid mapping variable."""
    grid_mapping_names = ds.cf.grid_mapping_names
    if list(grid_mapping_names) != ["geostationary"]:
        raise ValueError(
            f"expected a single 'geostationary' grid mapping, found {grid_mapping_names}"
        )
    (var_name,) = grid_mapping_names["geostationary"]
    attrs = ds[var_name].attrs

    globe = ccrs.Globe(
        semimajor_axis=attrs["semi_major_axis"],
        semiminor_axis=attrs["semi_minor_axis"],
    )
    return ccrs.Geostationary(
        central_longitude=attrs["longitude_of_projection_origin"],
        satellite_height=attrs["perspective_point_height"],
        sweep_axis=attrs["sweep_angle_axis"],
        globe=globe,
    )


def main():
    import matplotlib.pyplot as plt

    prefix = "s3://fci-mtg.level1c.zarr/fci-20250923.zarr/"
    opts = {
        "anon": True,
        "client_kwargs": {"endpoint_url": "https://s3.r1.cloud.eumetsat.int"},
    }
    dt = xr.open_datatree(prefix, consolidated=False, storage_options=opts)
    ds = dt["channels_at_2km_resolution"].to_dataset()

    crs = geostationary_crs(ds)
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": crs})
    ax.coastlines()
    ax.set_global()
    fig.savefig("geostationary_full_disk.png")


if __name__ == "__main__":
    main()
