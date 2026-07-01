import receiver

# public channel is a perfect channel !

def send_synchronization(clk):
    receiver.start_new_communication(clk)