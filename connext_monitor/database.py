import sqlite3

# TODO: actually implement a sqlite database class for model
class Database():
    def __init__(self):
        pass
    
    def insert_transfer(self, transfer):
        """
        Insert transfer (xcall event) to database
        """
        pass

    def update_transfer_reconcile(self, reconcile):
        """
        Update reconcile event to database
        """
        pass

    def update_transfer_executed(self, executed):
        """
        Update executed event to database
        """
        pass

    def get_all_transfer_after(self, time_start, time_end):
        """
        Get all transfer between time_start and time_end. Here, we use xcall block timestamp as transfer time .
        """
        pass    
