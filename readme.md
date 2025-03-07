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
The project requires the [2DMatGMM](https://github.com/Jaluus/2DMatGMM) library as a submodule.
```bash
# From the project root directory
pip install -e 2DMatGMM
```

### 3. Set up the Client
```bash
cd client
npm install
```

### 4. Configure Environment Variables
Create a `.env` file in the project root directory with the following content:
```plaintext
sim_test = False
motorControllerPort = "COM3"
perfControllerPort = "COM4"
```
Adjust the port values according to your setup.

## Running the Application

### Start the Backend Server
```bash
# From the project root
cd src
python main.py

# Or use the shorthand command
conda activate automatedTransfer && cd src && python main.py
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

## TODO: Get responses and commands sent over to the client
## Pase the json on the server side, start up a extraneous thread that runs the transfer program and then closes
## Get the program controlling the transfer station
## Get the flake hunting algorithm working
