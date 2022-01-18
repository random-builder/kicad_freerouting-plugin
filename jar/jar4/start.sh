#!/usr/bin/env bash

#
# invoke java app
#

here_dir=$(cd $(dirname "$0") && pwd)

module_path="$here_dir/freerouting-1.4.5.1.jar"

java -jar "$module_path"
