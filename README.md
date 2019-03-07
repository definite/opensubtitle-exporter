# OpenSubtitle Exporter
Export opensubtitle database to other formats such as CSV, Excel, or SQL.

## Utilities
### FileExtractor.py
Extract tar.gz files in <source_dir> and output to <output_dir>

```sh
python FileExtractor.py <source_dir> <out_dir>
```

Please note that `out_dir` should NOT be the same or the sub-directory of
`source_dir`. Otherwise this program takes longer to finish as it will also look
for source files in `out_dir` as well.