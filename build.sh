#!/bin/bash
# Build script
set -eo pipefail

build_tag=$1
name=nulpchatbot
node=$3
org=$4

# Define image name and tag
imageName="${name}"
imageTag="${build_tag}"

# Build Docker image
docker build -t "${org}/${imageName}:${imageTag}" .

# Create metadata.json with the relevant details
echo "{\"image_name\" : \"${imageName}\", \"image_tag\" : \"${imageTag}\", \"node_name\" : \"${node}\"}" > metadata.json
