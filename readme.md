# Automated Transfer Program

Created by Austin Wu for the Yasuda Lab at Cornell. The intention is to make a platform for 2d material automation platforms that can interface with any station, run flake searching (and potentially automated stacking algorithms), and also control the station automatically.

## Setup

First install miniconda. Make sure locally and add path to env

To create and activate a conda enviroment, run

```
conda create -n automatedTransfer python=3.11.9
conda activate automatedTransfer
```

Then `cd` to the directory and run

```
pip install -r ./requirements.txt
```

crate .env in directory and add this info

```
.env is:
sim_test = False
motorControllerPort = "COM3"
perfControllerPort = "COM4"
```

Now this library should be downloaded as an submodule <https://github.com/Jaluus/2DMatGMM>. Go to parent folder of 2dMatGMM (Home directory) and run

```
pip install -e 2DMatGMM
```

Now to install the client run:

```
cd client
npm install
cd ..
```

## Running the program

In order to start the backend server run:

```
cd src
python main.py
```

Or shorthandedly

```
conda activate automatedTransfer && cd src && python main.py
```

Ensure the `.env` file is correct for your setup. Now in another terminal to enable to ui:

```
cd client
npm run dev
```

If having issues with conda on windows (although I suggest using wsl):

```
set-executionpolicy unrestricted
conda init powershell
```
