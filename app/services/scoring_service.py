# this program will be imported in realtime_bridge and added to the stop() method (????)

def read_msg(user_id, conv_id):
    # read from db
    # output: dict with conv 
    pass

def scoring(user_id, conv_id):
    conver = read_msg(user_id, conv_id)
    # input: dict (resulting from read_msg)
    # output: None (insert metrics to DB during execution)
    pass

