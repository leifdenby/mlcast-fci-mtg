

# 4/9/2026

changed to use new sample dataset stored at https://s3.r1.cloud.eumetsat.int/fci-mtg.level1c.zarr/fci-20250923.zarr/, which has following changes since the previous sample:
  - 6 samples in time ending at 2025-09-23T23:50:07
  - has time coordinate un-chunked
  - contains consolidated metadata
  - has zarr groups for the each resolution (1km and 2km) renamed to `channels_at_1km_resolution` and `channels_at_2km_resolution` respectively
  
New notebook checks the following:
  - that new zarr groups are present
  - that the time coordinate is un-chunked so we can load all time steps at once (and construct time index at load)
  - that the data can be subsetted by index number and by value, and that both methods yield the same result
  
New notebook demonstrates the following:
  - loading all zarr groups as a datatree and lifting the time coordinate to the root of the datatree