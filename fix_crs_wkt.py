"""Add a missing BBOX to the CRS WKT stored on the FCI-MTG L1C zarr datasets.

The `crs_wkt` stored on the `spatial_ref` grid-mapping variable has no `USAGE`/
`BBOX` element, which some plotting libraries (cartopy, GeoViews, ...) rely on
to determine a CRS's `area_of_use`. WKT2's BBOX is always geographic degrees
(`[south_lat, west_lon, north_lat, east_lon]`), independent of the CRS's own
projected units, so it can't be derived from the x/y extent alone. Instead we
take it straight from the dataset's own `latitude`/`longitude` variables,
which are NaN outside the visible disk.
"""

import xarray as xr

BBOX_AREA_NAME = "Earth visible from geostationary satellite."


def fix_crs_wkt(ds: xr.Dataset) -> str:
    """Return `ds`'s CRS WKT with a BBOX (area of use) added, if missing."""
    wkt = ds["spatial_ref"].attrs["crs_wkt"].rstrip()

    if "BBOX[" in wkt:
        return wkt

    lat_min = float(ds["latitude"].min(skipna=True))
    lat_max = float(ds["latitude"].max(skipna=True))
    lon_min = float(ds["longitude"].min(skipna=True))
    lon_max = float(ds["longitude"].max(skipna=True))

    if not wkt.endswith("]"):
        raise ValueError(f"unexpected CRS WKT format, does not end with ']': {wkt!r}")

    usage = (
        ',USAGE[SCOPE["Full disk imagery."],'
        f'AREA["{BBOX_AREA_NAME}"],'
        f"BBOX[{lat_min:.6f},{lon_min:.6f},{lat_max:.6f},{lon_max:.6f}]]"
    )

    # insert as a sibling of the CRS's existing children, just before its final closing bracket
    return wkt[:-1] + usage + "]"


def main():
    prefix = "s3://fci-mtg.level1c.zarr/fci-20250923.zarr/"
    opts = {
        "anon": True,
        "client_kwargs": {"endpoint_url": "https://s3.r1.cloud.eumetsat.int"},
    }
    dt = xr.open_datatree(prefix, consolidated=False, storage_options=opts)
    ds = dt["channels_at_2km_resolution"].to_dataset()

    wkt = fix_crs_wkt(ds)
    print(wkt)

    from pyproj import CRS

    print()
    print("area_of_use:", CRS.from_wkt(wkt).area_of_use)


if __name__ == "__main__":
    main()
