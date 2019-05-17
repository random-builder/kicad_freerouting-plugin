#!/usr/bin/env bash

#
# provision jar artifact
#

version="2.0.0.20190517195349"

source="https://dl.bintray.com/random-maven/maven/com/carrotgarden/kicad/kicad-freerouting/$version/kicad-freerouting-$version.jar"

here_dir=$(cd $(dirname "$0") && pwd)

echo "### fetch"
wget -v -O $here_dir/FreeRouting.jar $source
