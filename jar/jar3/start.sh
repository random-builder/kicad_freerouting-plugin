#!/usr/bin/env bash

#
# invoke java app
#

here_dir=$(cd $(dirname "$0") && pwd)

module_path="$here_dir/FreeRouting.jar"

java -jar "$module_path"
