"""Open the FCI-MTG L1C zarr datatree and lift the shared `time` coordinate to the root.

The `channels_at_1km_resolution` and `channels_at_2km_resolution` groups each carry
their own (identical) `time` coordinate. This moves it to the root group so it's
defined once and inherited by both children, instead of being duplicated.
"""

import xarray as xr

PREFIX = "s3://fci-mtg.level1c.zarr/fci-20250923.zarr/"
STORAGE_OPTIONS = {
    "anon": True,
    "client_kwargs": {"endpoint_url": "https://s3.r1.cloud.eumetsat.int"},
}

GROUPS = ["channels_at_1km_resolution", "channels_at_2km_resolution"]


def lift_shared_time(dt: xr.DataTree, groups: list[str] = GROUPS) -> xr.DataTree:
    """Move an identical `time` coordinate from each child group up to the root."""
    reference = dt[groups[0]]["time"]
    for name in groups[1:]:
        if not dt[name]["time"].identical(reference):
            raise ValueError(f"time coordinate on '{name}' differs from '{groups[0]}'")

    for name in groups:
        dt[name].dataset = dt[name].dataset.drop_vars("time")

    dt.dataset = dt.dataset.assign_coords(time=reference)
    return dt


def open_datatree() -> xr.DataTree:
    return xr.open_datatree(
        PREFIX,
        consolidated=False,
        storage_options=STORAGE_OPTIONS,
    )


def main():
    dt = open_datatree()
    dt = lift_shared_time(dt)
    print(dt)


if __name__ == "__main__":
    main()
