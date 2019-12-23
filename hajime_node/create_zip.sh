echo "Bootstrap node."
cd bootstrap
if test -f "bootstrap.zip"; then
  rm "bootstrap.zip"
fi
zip bootstrap.zip -r __main__.py -r kademlia 

echo "implant module."
cd ../implant
if test -f "implant.zip"; then
  rm "implant.zip"
fi
zip implant.zip -r __main__.py kademlia
cd ..
