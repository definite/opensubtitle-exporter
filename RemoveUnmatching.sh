# Written by Chester Cheng (2019) <chester.cheng@uq.edu.au>

# This script removes all the unmatching English-Chinese xml files in OpenSubtitle2018 projects. 

# Creating a temporary file list
cat en-zh_cn.xml.gz.tmp | grep fromDoc > filelist.txt
# Making a temporary folder to store the files to be kept
mkdir tmp
# Copying wanted English files into the tmp folder, while keeping the file structure.
cp --parents `cut -d " " -f 3 filelist.txt | sed -e 's/fromDoc="/xml\//' | sed -e 's/"//'` tmp/
# Copying wanted Chinese files into the tmp folder, while keeping the file structure.
cp --parents `cut -d " " -f 4 filelist.txt | sed -e 's/toDoc="/xml\//' | sed -e 's/">//'` tmp/

# Listing the English/Chinese file sizes before and after.
# Listing numbers of English/Chinese files
echo "English file size before processing =" `du -sh xml/en/ | cut -f 1`
echo "English file size after processing =" `du -sh tmp/xml/en/ | cut -f 1`
echo "Chinese file size before processing =" `du -sh xml/zh_cn/ | cut -f 1`
echo "Chinese file size after processing =" `du -sh tmp/xml/zh_cn/ | cut -f 1`
echo
echo "Numbers of English files:" `ls -lR xml/en/ | grep xml.gz | wc -l`
echo "Numbers of Chinese files:" `ls -lR xml/zh_cn/ | grep xml.gz | wc -l`

# Removing the temporary file list
rm filelist.txt

# Replacing the xml/ with tmp/ -- the files we want to keep
rm -rf xml/
mv tmp/xml/ xml/
rm -rf tmp/

