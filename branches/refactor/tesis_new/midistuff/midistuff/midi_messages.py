class MidiMessage(object):
    def __init__(self, msg_args, method_name, time= 0):
        """
        params:
          msg_args :: [int]
        """
        self.time= time
        self.msg_args= msg_args
        self.method_name= method_name

    def apply(self, mof):
        """
        params:
          mof :: MidiOutStream
        """
        method= getattr(mof, self.method_name)
        try: method(*self.msg_args)
        except Exception, e: 
            print "WARNING: ", e.message
            import ipdb;ipdb.set_trace()

    def __repr__(self):
        return 'MidiMessage(%s, %s, %s)' % (repr(self.msg_args), repr(self.method_name), self.time)


class MidiMessageFactory(object):
    def __init__(self, msg_args, method_name, time= 0):
        self.time= time
        self.msg_args= msg_args
        self.method_name= method_name
    
    def get_message(self):
        return MidiMessage(self.msg_args, self.method_name, self.time)

class MidiControllerFactory(MidiMessageFactory):
    def __init__(self, msg_args, time):
        MidiMessageFactory.__init__(self, msg_args, 'continuous_controller', time)

    def bind_channel(self, channel):
        self.msg_args.insert(0, channel)
    
