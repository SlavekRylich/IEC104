import sys
import time
 
 
class Timeout():
    
    
    def __init__(self, seconds) -> None:
        self.seconds = seconds
        self.die_after = time.time() + self.seconds
        
    
    def __enter__(self):
        self.die_after = time.time() + self.seconds
        return self
    
    
    def __exit__(*exc_info):
        pass
    
    def start(self):
        self.die_after = time.time() + self.seconds
        return self
        
    @property
    def timed_out(self):
        return time.time() > self.die_after
    
    
    
    
#     Here's a single-threaded usage example:

# with timeout(1) as t:
#     while True: # this will take a long time without a timeout
#         # periodically check for timeouts
#         if t.timed_out:
#             break # or raise an exception
#         # do some "useful" work
#         print "."
#         time.sleep(0.2)


#           	and a multithreaded one:

# import thread
# def print_for_n_secs(string, seconds):
#     with timeout(seconds) as t:
#         while True:
#             if t.timed_out:
#                 break # or raise an exception
#             print string,
#             time.sleep(0.5)

# for i in xrange(5):
#     thread.start_new_thread(print_for_n_secs,
#                             ('thread%d' % (i,), 2))
#     time.sleep(0.25)