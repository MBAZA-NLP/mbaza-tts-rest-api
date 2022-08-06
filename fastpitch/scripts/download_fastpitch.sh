#!/usr/bin/env bash

set -e

: ${MODEL_DIR:="pretrained_models/fastpitch"}
MODEL=$2
MODEL_ZIP="${MODEL}.zip"
#https://api.ngc.nvidia.com/v2/models/nvidia/fastpitch_pyt_amp_ckpt_v1_1/versions/21.05.0/zip

mkdir -p "$MODEL_DIR"

if [ ! -f "${MODEL_DIR}/${MODEL_ZIP}" ]; then
  echo "Downloading ${MODEL_ZIP} ..."
  gdown -q -O ${MODEL_DIR}/${MODEL_ZIP} $1 \
       || { echo "ERROR: Failed to download ${MODEL_ZIP} from NGC"; exit 1; }
fi

if [ ! -f "${MODEL_DIR}/${MODEL}" ]; then
  echo "Extracting ${MODEL} ..."
  unzip -qo ${MODEL_DIR}/${MODEL_ZIP} -d ${MODEL_DIR} \
        || { echo "ERROR: Failed to extract ${MODEL_ZIP}"; exit 1; }

  echo "OK"

else
  echo "${MODEL} already downloaded."
fi
