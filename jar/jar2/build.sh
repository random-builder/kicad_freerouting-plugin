#!/usr/bin/env bash

#
# provision jar artifact
#

source="https://github.com/Engidea/FreeRoutingNew/raw/master/deploy/FreeRouting.jar"

here_dir=$(cd $(dirname "$0") && pwd)

echo "### fetch"
wget -v -nc -O $here_dir/FreeRouting.jar $source
