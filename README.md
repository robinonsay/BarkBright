# BarkBright: Open Source Voice/Text Dialogue Home Automation
BarkBright is an open-source voice enabled conversational system allowing for home IoT control. BarkBright utilizes natural language processing techniques inorder to deliver an intuitive and user-friendly expierence.

## Features
* **Voice control:** BarkBright uses [vosk](https://alphacephei.com/vosk/) offline Automatic Speech Recognition (ASR)
* **Lightweight:** BarkBright is designed to run on embedded architectures like the Raspberry Pi and BeagleBone Black, therefore it **does not require a GPU to train or run the models**
* **Pretrained Intent Model:** BarkBright has a [pretrained model](barkbright/models/assets) availble for use, as well as all the model details so you can build on top of the architecture!

## *Future Features*

*  **Dialogue-based interaction:** Users can engage in a conversational manner with BarkBright. This allows for intuitive control of home IoT
* **Dataset Creation and Model Updating**: BarkBright can create a dataset based on your interactions with Human-In-The-Loop feedback. This can be used to update or retrain the model completly on commonly used phrases!

## Getting Started

* Clone the repo:
    ```
    git clone https://github.com/robinonsay/BarkBright.git
    ```
* Install Dependencies
    ```
    pip3 install -r requirements.txt
    ```
* Download the [ASR model](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip) to `BarkBright/barkbright/models/assets/`
* Run the demo
    ```
    python -m barkbright
    ```
* Run the command line chat interface demo
    ```
    python -m barkbright --cli
    ```

## Demo
The demo will use vosk and [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) to record and transcribe your voice input and use the intent model to predict the intent.

## CLI Chat Interface

BarkBright features a text input CLI interface for debugging and dataset creation. If BarkBright responds incorrectly, you can correct the system by inputing `<no>`. Otherwise, to end the session just hit enter (i.e. empty input)

## License
Copyright 2023 Robin Onsay

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
