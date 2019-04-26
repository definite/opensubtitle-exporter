# OpenSubtitle Exporter
Export [opensubtitles](http://www.opensubtitles.org) database to other formats
such as CSV, Excel, or SQL.

The XML is from http://opus.nlpl.eu/OpenSubtitles-v2018.php

## Utilities
### RemoveUnmatching.sh
This script removes the documents that do not exist in matching document
(`en-zh_cn.xml.gz.tmp`). It should be run at the parent of `xml/`
```sh
./RemoveUnmatching.sh
```

### FileExtractor.py
Extract tar.gz files in <source_dir> and output to <output_dir>

```sh
python FileExtractor.py <source_dir> <out_dir>
```

Please note that `out_dir` should NOT be the same or the sub-directory of
`source_dir`. Otherwise this program takes longer to finish as it will also look
for source files in `out_dir` as well.

### XmlExporter
Export from XML to database.

```sh
python XmlExporter db [Options] <language> <xml_directory>
```

