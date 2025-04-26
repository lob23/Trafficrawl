#!/bin/bash

mkdir -p easylist

echo "----Downloading easylist----"
curl -L https://easylist.to/easylist/easylist.txt -o easylist/easylist.txt

echo "----Downloading easyprivacy----"
curl -L https://easylist.to/easylist/easyprivacy.txt -o easylist/easyprivacy.txt

echo "Downloads completed. Files saved in 'easylist/' folder."