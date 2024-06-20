setup:
 
 install miniconda
 locallly and add path to env

in cmd not powershell 
conda create -n automatedTransfer python=3.11.9
conda activate automatedTransfer

cd to directory
and do
pip install -r ./requirements.txt

crate .env in directory and add this info
.env is:
sim_test = False
motorControllerPort = "COM3"
perfControllerPort = "COM4"

then download this
https://github.com/Jaluus/2DMatGMM

go to parent folder of 2dMatGMM
pip install -e 2DMatGMM

go to main folder in this
cd client
npm install 
cd ..

to run:

cd src
python main.py

another terminal:
cd client
npm run dev

conda activate automatedTransfer && cd src && python main.py