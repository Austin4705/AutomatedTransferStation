# Automated Transfer Program

## Overview
This platform, developed by Austin Wu for the Yasuda Lab at Cornell, is designed for 2D material automation. It provides:
- Interface capabilities with various stations
- Flake searching functionality
- Potential automated stacking algorithms
- Automated station control

## Prerequisites
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (Make sure it's installed and added to your PATH)
- Python 3.11.9
- Node.js and npm (for the client application)

## Installation

### 1. Set up the Python Environment
```bash
# Create and activate a new conda environment
conda create -n automatedTransfer python=3.11.9
conda activate automatedTransfer

# Install dependencies
cd /path/to/project
pip install -r requirements.txt
```

### 2. Install 2DMatGMM
The project requires the [2DMatGMM](https://github.com/Austin4705/2DMatGMM) library as a submodule. Either use the submoudle recurisve or git clone it. Note please use my forked version.
```bash
# From the project root directory
git submodule update --init --recursive
git clone https://github.com/Austin4705/2DMatGMM

pip install -e 2DMatGMM
```

### 3. Set up the Client
```bash
cd client
npm install
```

### 4. Configure Specifci Environment 
Create a `config.json` file in the project root directory with the following content:
```plaintext
{
    "transfer_station": "hqGrapheneServer"
}
```
Now if you are using a hq graphene transfer station, do a couple things. Ensure the software is updated to the latest version, it should have the latest version of the command server. Ensure that (the imaging source drivers)[https://www.theimagingsource.com/en-us/support/download/icwdmuvccamtis33u-5.3.0.2793/] are properly installed


(Or "base" if you want to do the virtual ones). Adjust the port values according to your setup.

## Running the Application

### Start the Backend Server
If on a hq graphene system ensure that the software is started and then goto file -> run command server 

```bash
# From the project root
cd src
python main.py

# Or use the shorthand command
conda activate automatedTransfer && cd src && python main.py

#Alternatively for windows you can run 
.\run.bat
```

### Launch the User Interface
In a separate terminal:
```bash
cd client
npm run dev
```

## Troubleshooting

### Windows-specific Issues
If you encounter Conda-related issues on Windows (WSL is recommended instead):
```powershell
Set-ExecutionPolicy Unrestricted
conda init powershell
```

### Previously Useful Commands
```python
&scripts.traceOver(ts, 4, 0.7, 0.7, 2)
&ts.vaccum_on()

&Camera.save_image(Camera.matGMM2DTransform(Camera.global_list[0].get_frame()))
&Camera.save_image(Camera.global_list[0].get_frame())
```

cd src ; conda activate automatedTransfer ; main.py 
## Contributing
For questions or contributions, please contact the Yasuda Lab at Cornell.

## License
[Add your license information here]

## TODO and BUGS
    -Get the program controlling the other transfer station (get upstairs transfer station working)
    -Get the flake hunting algorithm working
    -Far away: get theta detection and outlining for flakes
    
## Done:
    - Fix bug with commands and such not sending properly from the queue (seems to be working?)
    Get position to auto initalize 
    -button to auto scan and draw
    -log is broken
    -flake hunting poll without button
    -get re-localization feature working

