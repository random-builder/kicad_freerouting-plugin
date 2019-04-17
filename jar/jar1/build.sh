#!/usr/bin/env bash

#
# provision jar artifact
#

source="https://layouteditor.com/releases/20190401/layout-20190401-Linux.x86_64.tar.bz2"

here_dir=$(cd $(dirname "$0") && pwd)

package="$here_dir/package.tmpdir"

artifact_path="layout/bin/freeRouting.jar"
artifact_source="$package/$artifact_path"
artifact_target="$here_dir/FreeRouting.jar"

mkdir -p $package

echo "### fetch"
wget -v -nc -O $here_dir/package.tar.bz2 $source

echo "### unpack"
tar -v -x -j -C $package -f $here_dir/package.tar.bz2 $artifact_path

echo "### deploy"
cp -v -f $artifact_source $artifact_target
