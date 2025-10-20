from transfer_station import Transfer_Station

class TransferStationPrior(Transfer_Station):
    def __init__(self):
        super().__init__()
        self.type = "prior"
