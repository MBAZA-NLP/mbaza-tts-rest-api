Run in docker container:
> make run-docker-eng-cpu

The following variables can be set using Env variables in corresponding docker-compose files:
docker-compose-eng-gpu.yml or docker-compose-eng-cpu.yml
```
environment:
  - THREADS=2
  - PROCESSES=1
  - SRV_HOST=0.0.0.0
  - SRV_PORT=6901
  - API_USERNAME=mbaza
  - API_PASSWORD=ttssecret
  - APP_SENTENCE_MAX_WORDS=40
  - APP_SENTENCE_INFER_BATCH_SIZE=10
```

Run on local: 
```
pip install "pip<22" 
git clone https://github.com/NVIDIA/DeepLearningExamples.git NVIDIADeepLearning
cd NVIDIADeepLearning && git checkout -b tts a43ffd01cb002b23a98c97c3c5a231e24a57fa71
cd ..

#(only for KIN language)
cp tts/fastpitch/overwrite/common/text/* NVIDIADeepLearning/PyTorch/SpeechSynthesis/FastPitch/common/text/.
 
pip install -r NVIDIADeepLearning/PyTorch/SpeechSynthesis/FastPitch/requirements.txt
make dep-sync
make run-local
```

Access REST ui http://localhost:6901 and login with API_USERNAME/API_PASSWORD
